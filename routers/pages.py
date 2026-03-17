from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from core.pdf_renderer import PDFRenderer
from core.state import project_manager as pm

router = APIRouter(prefix="/api/projects", tags=["pages"])
renderer = PDFRenderer()


@router.get("/{project_id}/pages/{page_num}/image")
def page_image(project_id: str, page_num: int, dpi: int = Query(default=150, ge=100, le=300)):
    try:
        meta = pm.get_project(project_id)
        if page_num < 1 or page_num > meta.page_count:
            raise HTTPException(status_code=404, detail="Page number out of range")
        pdir = pm.project_path(project_id)
        cached = pdir / "pages" / f"{page_num:04d}.jpg"
        if cached.exists() and dpi == meta.render_dpi:
            data = cached.read_bytes()
            return Response(content=data, media_type="image/jpeg")

        data, width, height = renderer.render_page(pdir / "source.pdf", page_num, dpi, cached if dpi == meta.render_dpi else None)
        return Response(content=data, media_type="image/jpeg", headers={"X-Page-Width": str(width), "X-Page-Height": str(height)})
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{project_id}/pages/{page_num}/thumbnail")
def page_thumbnail(project_id: str, page_num: int):
    try:
        meta = pm.get_project(project_id)
        if page_num < 1 or page_num > meta.page_count:
            raise HTTPException(status_code=404, detail="Page number out of range")
        pdir = pm.project_path(project_id)
        cached = pdir / "pages" / f"{page_num:04d}.jpg"
        if not cached.exists():
            renderer.render_page(pdir / "source.pdf", page_num, meta.render_dpi, cached)
        return Response(content=renderer.thumbnail(cached), media_type="image/jpeg")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
