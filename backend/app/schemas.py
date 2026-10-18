from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Level = Literal["debug", "info", "warning", "error", "critical"]
Severity = Literal["low", "medium", "high", "critical"]
Status = Literal["open", "acknowledged", "resolved"]


class EventIn(BaseModel):
    source: str = Field(min_length=1, max_length=100)
    level: Level
    message: str = Field(min_length=1, max_length=2000)
    context: dict | None = None


class EventOut(EventIn):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class IncidentIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    source: str | None = Field(default=None, max_length=100)
    severity: Severity = "medium"


class IncidentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    severity: Severity | None = None
    status: Status | None = None


class IncidentOut(BaseModel):
    id: int
    title: str
    source: str | None
    severity: Severity
    status: Status
    auto_created: bool
    created_at: datetime
    resolved_at: datetime | None

    model_config = {"from_attributes": True}
