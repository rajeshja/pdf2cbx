import shutil

from fastapi import APIRouter, HTTPException

from config import settings
from core.state import project_manager as pm
from core.state import task_manager as tm

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/tasks/{task_id}")
def get_task(task_id: str):
    try:
        return tm.get(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/settings")
def get_settings():
    return {
        "projects_dir": str(settings.projects_dir),
        "render_dpi": settings.render_dpi,
        "default_jpeg_quality": settings.default_jpeg_quality,
        "max_undo_steps": settings.max_undo_steps,
        "detection_model": settings.detection_model,
        "detection_confidence_threshold": settings.detection_confidence_threshold,
    }


@router.patch("/settings")
def patch_settings(body: dict):
    mutable = get_settings()
    mutable.update(body)
    return mutable


@router.delete("/cache")
def clear_cache():
    deleted = 0
    freed = 0
    for project in pm.list_projects():
        pdir = pm.project_path(project.id)
        pages = pdir / "pages"
        for f in pages.glob("*.jpg"):
            freed += f.stat().st_size
            f.unlink()
            deleted += 1
        thumbs = pdir / "thumbs"
        if thumbs.exists():
            shutil.rmtree(thumbs)
    return {"deleted_files": deleted, "freed_bytes": freed}
