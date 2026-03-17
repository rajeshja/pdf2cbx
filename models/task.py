from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TaskStatus(BaseModel):
    id: str
    type: str
    status: str = "queued"
    progress: float = 0.0
    progress_label: str = ""
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[dict[str, Any]] = None


class ExportRequest(BaseModel):
    jpeg_quality: int = 85
    page_from: int = 1
    page_to: Optional[int] = None
