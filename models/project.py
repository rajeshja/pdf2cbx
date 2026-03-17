from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProjectMeta(BaseModel):
    id: str
    title: str
    source_filename: str
    source_size_bytes: int
    page_count: int
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    last_page_viewed: int = 1
    render_dpi: int = 150
    exported_at: Optional[datetime] = None
    export_filename: Optional[str] = None
    pages_detected: list[int] = Field(default_factory=list)
    pages_edited: list[int] = Field(default_factory=list)


class ProjectListItem(BaseModel):
    id: str
    title: str
    page_count: int
    created_at: datetime
    updated_at: datetime
    last_page_viewed: int
    source_size_bytes: int
    pages_detected_count: int
    pages_edited_count: int
    exported_at: Optional[datetime]


class ProjectPatch(BaseModel):
    title: str
