from typing import Literal, Optional

from pydantic import BaseModel, Field

PanelType = Literal["text", "figure", "table", "header", "footer", "unknown"]


class Panel(BaseModel):
    id: Optional[str] = None
    order: int
    x: int
    y: int
    width: int
    height: int
    type: PanelType = "text"
    include: bool = True
    confidence: Optional[float] = None
    label: str = ""


class PagePanels(BaseModel):
    page: int
    source_width: int
    source_height: int
    detection_run: bool = False
    detection_model: str = "opencv"
    detection_confidence_threshold: float = 0.5
    manually_edited: bool = False
    panels: list[Panel] = Field(default_factory=list)


class DetectRequest(BaseModel):
    confidence_threshold: float = 0.5
    model: str = "opencv"


class TemplateCreateRequest(BaseModel):
    source_page: int
    name: str


class TemplateApplyRequest(BaseModel):
    page_from: int
    page_to: int
    overwrite_edited: bool = False
