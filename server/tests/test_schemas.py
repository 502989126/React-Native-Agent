from datetime import datetime

import pytest
from pydantic import ValidationError

from server.app.schemas import CreateEventAction, CreateEventPayload


def valid_payload() -> dict:
    return {
        "title": "和小王吃饭",
        "start_at": "2026-08-29T18:30:00+08:00",
        "end_at": "2026-08-29T19:30:00+08:00",
        "timezone": "Asia/Shanghai",
        "location": "静安寺",
    }


def test_create_event_payload_accepts_valid_data() -> None:
    payload = CreateEventPayload.model_validate(valid_payload())

    assert payload.title == "和小王吃饭"
    assert payload.start_at.tzinfo is not None
    assert payload.timezone == "Asia/Shanghai"


def test_create_event_payload_rejects_naive_datetime() -> None:
    data = valid_payload()
    data["start_at"] = datetime(2026, 8, 29, 18, 30)

    with pytest.raises(ValidationError, match="start_at must include a timezone offset"):
        CreateEventPayload.model_validate(data)


def test_create_event_payload_rejects_invalid_time_range() -> None:
    data = valid_payload()
    data["end_at"] = "2026-08-29T18:00:00+08:00"

    with pytest.raises(ValidationError, match="end_at must be later than start_at"):
        CreateEventPayload.model_validate(data)


def test_create_event_payload_rejects_unknown_timezone() -> None:
    data = valid_payload()
    data["timezone"] = "Mars/Colony-1"

    with pytest.raises(ValidationError, match="valid IANA timezone"):
        CreateEventPayload.model_validate(data)


def test_action_always_requires_confirmation() -> None:
    action = CreateEventAction(payload=CreateEventPayload.model_validate(valid_payload()))

    assert action.type == "CREATE_EVENT"
    assert action.status == "PROPOSED"
    assert action.requires_confirmation is True


def test_action_rejects_false_confirmation_flag() -> None:
    data = {
        "payload": valid_payload(),
        "requires_confirmation": False,
    }

    with pytest.raises(ValidationError):
        CreateEventAction.model_validate(data)
