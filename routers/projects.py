import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from config import settings
from core.state import project_manager as pm
from models.project import ProjectPatch

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("")
def list_projects():
    return pm.list_projects()


@router.post("", status_code=201)
async def create_project(file: UploadFile = File(...), title: str | None = Form(default=None)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File is not a valid PDF")

    content = await file.read()
    if len(content) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds max upload size")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        return pm.create_project(tmp_path, file.filename, title)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{project_id}")
def get_project(project_id: str):
    try:
        return pm.get_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{project_id}")
def patch_project(project_id: str, body: ProjectPatch):
    try:
        return pm.update_title(project_id, body.title)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str):
    try:
        pm.delete_project(project_id)
        return Response(status_code=204)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
