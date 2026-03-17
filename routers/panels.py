import asyncio
import uuid

from fastapi import APIRouter, HTTPException
from PIL import Image

from config import settings
from core.layout_detector import LayoutDetector
from core.panel_store import PanelStore
from core.pdf_renderer import PDFRenderer
from core.state import project_manager as pm
from core.state import task_manager as tm
from models.panel import DetectRequest, Panel, TemplateApplyRequest, TemplateCreateRequest

router = APIRouter(prefix="/api/projects", tags=["panels"])
detector = LayoutDetector()
renderer = PDFRenderer()


@router.get("/{project_id}/pages/{page_num}/panels")
def get_panels(project_id: str, page_num: int):
    try:
        meta = pm.get_project(project_id)
        if page_num < 1 or page_num > meta.page_count:
            raise HTTPException(status_code=404, detail="Page number out of range")
        pdir = pm.project_path(project_id)
        store = PanelStore(pdir)
        page = store.get_page(page_num)
        if page is not None:
            return page

        image_path = pdir / "pages" / f"{page_num:04d}.jpg"
        if not image_path.exists():
            renderer.render_page(pdir / "source.pdf", page_num, meta.render_dpi, image_path)

        detected = detector.detect(page_num, image_path, settings.detection_confidence_threshold, settings.detection_model)
        store.save_page(detected)
        if page_num not in meta.pages_detected:
            meta.pages_detected.append(page_num)
            pm.write_project(meta)
        return detected
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{project_id}/pages/{page_num}/panels")
def put_panels(project_id: str, page_num: int, panels: list[Panel]):
    try:
        pdir = pm.project_path(project_id)
        store = PanelStore(pdir)
        existing = store.get_page(page_num)
        if existing is None:
            raise HTTPException(status_code=400, detail="Page must be rendered/detected first")
        saved = store.save_from_panels(page_num, existing.source_width, existing.source_height, panels)
        meta = pm.get_project(project_id)
        if page_num not in meta.pages_edited:
            meta.pages_edited.append(page_num)
        pm.write_project(meta)
        return saved
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{project_id}/pages/{page_num}/detect", status_code=202)
async def detect_panels(project_id: str, page_num: int, body: DetectRequest):
    try:
        meta = pm.get_project(project_id)
        pdir = pm.project_path(project_id)
        task_id = f"det-{uuid.uuid4().hex[:8]}"
        tm.create(task_id, "detection")

        def _detect(task):
            image_path = pdir / "pages" / f"{page_num:04d}.jpg"
            if not image_path.exists():
                renderer.render_page(pdir / "source.pdf", page_num, meta.render_dpi, image_path)
            page = detector.detect(page_num, image_path, body.confidence_threshold, body.model)
            PanelStore(pdir).save_page(page)
            return {"page": page_num, "panel_count": len(page.panels)}

        asyncio.create_task(tm.run(task_id, _detect))
        return {"task_id": task_id, "status": "running"}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{project_id}/templates", status_code=201)
def create_template(project_id: str, body: TemplateCreateRequest):
    try:
        pdir = pm.project_path(project_id)
        store = PanelStore(pdir)
        src = store.get_page(body.source_page)
        if src is None:
            raise HTTPException(status_code=404, detail="Source page panels not found")
        return store.create_template(body.source_page, body.name, src.panels, src.source_width, src.source_height)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{project_id}/templates/{template_id}/apply")
def apply_template(project_id: str, template_id: str, body: TemplateApplyRequest):
    try:
        meta = pm.get_project(project_id)
        pdir = pm.project_path(project_id)
        store = PanelStore(pdir)
        applied: list[int] = []
        skipped: list[int] = []

        for page in range(body.page_from, body.page_to + 1):
            if page < 1 or page > meta.page_count:
                continue
            existing = store.get_page(page)
            if existing is not None and existing.manually_edited and not body.overwrite_edited:
                skipped.append(page)
                continue
            image_path = pdir / "pages" / f"{page:04d}.jpg"
            if not image_path.exists():
                renderer.render_page(pdir / "source.pdf", page, meta.render_dpi, image_path)
            with Image.open(image_path) as im:
                w, h = im.size
            store.apply_template(template_id, page, w, h)
            applied.append(page)

        return {"applied_to": applied, "skipped": skipped}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
