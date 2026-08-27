"""Domain schemas for the first CREATE_EVENT action."""

from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CreateEventPayload(BaseModel):
    """Fields required to create one calendar event."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=120)
    start_at: datetime
    end_at: datetime
    timezone: str = Field(min_length=1, max_length=64)
    all_day: bool = False
    location: str | None = Field(default=None, max_length=240)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title must not be blank")
        return value

    @field_validator("timezone")
    @classmethod
    def timezone_must_be_iana_name(cls, value: str) -> str:
        value = value.strip()
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("timezone must be a valid IANA timezone") from exc
        return value

    @model_validator(mode="after")
    def validate_dates(self) -> "CreateEventPayload":
        for field_name, value in (
            ("start_at", self.start_at),
            ("end_at", self.end_at),
        ):
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"{field_name} must include a timezone offset")

        if self.end_at <= self.start_at:
            raise ValueError("end_at must be later than start_at")

        return self


class CreateEventAction(BaseModel):
    """A server-owned proposal shown to the user before execution."""

    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    type: Literal["CREATE_EVENT"] = "CREATE_EVENT"
    status: Literal["PROPOSED"] = "PROPOSED"
    requires_confirmation: Literal[True] = True
    payload: CreateEventPayload
    assumptions: list[str] = Field(default_factory=list)
