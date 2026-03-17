from pathlib import Path

from fastapi.testclient import TestClient

import app as app_module
from models.project import ProjectMeta
from routers import export as export_router


def test_export_endpoint_starts_task(monkeypatch, tmp_path: Path):
    project_id = "proj-1"
    project_dir = tmp_path / project_id
    (project_dir / "output").mkdir(parents=True)

    meta = ProjectMeta(
        id=project_id,
        title="Book",
        source_filename="book.pdf",
        source_size_bytes=1,
        page_count=2,
    )

    monkeypatch.setattr(export_router.pm, "get_project", lambda pid: meta)
    monkeypatch.setattr(export_router.pm, "project_path", lambda pid: project_dir)
    monkeypatch.setattr(export_router.pm, "write_project", lambda _meta: None)

    def fake_export(_meta, _pdir, _quality, _page_from, _page_to, _task):
        return {"output_filename": "Book.cbz", "panel_count": 1, "file_size_bytes": 123}

    monkeypatch.setattr(export_router.exporter, "export", fake_export)
    export_router.tm.tasks.clear()

    client = TestClient(app_module.app)
    response = client.post(f"/api/projects/{project_id}/export", json={"jpeg_quality": 85, "page_from": 1, "page_to": 2})

    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "running"
    assert payload["task_id"].startswith("exp-")
