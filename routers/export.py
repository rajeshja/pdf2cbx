import asyncio
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from core.cbz_exporter import CBZExporter
from core.state import project_manager as pm
from core.state import task_manager as tm
from models.task import ExportRequest

router = APIRouter(prefix="/api/projects", tags=["export"])
exporter = CBZExporter()


@router.post("/{project_id}/export", status_code=202)
def export_project(project_id: str, body: ExportRequest):
    try:
        meta = pm.get_project(project_id)
        pdir = pm.project_path(project_id)
        task_id = f"exp-{uuid.uuid4().hex[:8]}"
        tm.create(task_id, "export")
        page_to = body.page_to or meta.page_count

        def _export(task):
            result = exporter.export(meta, pdir, body.jpeg_quality, body.page_from, page_to, task)
            meta.exported_at = datetime.now(timezone.utc)
            meta.export_filename = result["output_filename"]
            pm.write_project(meta)
            return result

        asyncio.create_task(tm.run(task_id, _export))
        return {"task_id": task_id, "status": "running"}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{project_id}/export/download")
def download_export(project_id: str):
    try:
        meta = pm.get_project(project_id)
        if not meta.export_filename:
            raise HTTPException(status_code=404, detail="No export has been completed for this project")
        pdir = pm.project_path(project_id)
        out = pdir / "output" / meta.export_filename
        if not out.exists():
            raise HTTPException(status_code=404, detail="Export file missing")
        return FileResponse(path=out, media_type="application/zip", filename=meta.export_filename)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
