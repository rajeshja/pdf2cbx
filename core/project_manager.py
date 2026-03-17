import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

import fitz

from config import settings
from models.project import ProjectListItem, ProjectMeta


class ProjectManager:
    def __init__(self, projects_dir: Path | None = None):
        self.projects_dir = projects_dir or settings.projects_dir
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def _project_dir(self, project_id: str) -> Path:
        return self.projects_dir / project_id

    def _project_json(self, project_id: str) -> Path:
        return self._project_dir(project_id) / "project.json"

    def _now(self):
        return datetime.now(timezone.utc)

    def create_project(self, pdf_path: Path, source_filename: str, title: str | None = None) -> ProjectMeta:
        project_id = str(uuid.uuid4())
        project_dir = self._project_dir(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "pages").mkdir(exist_ok=True)
        (project_dir / "output").mkdir(exist_ok=True)
        (project_dir / "templates").mkdir(exist_ok=True)

        source_target = project_dir / "source.pdf"
        shutil.move(str(pdf_path), source_target)
        with fitz.open(source_target) as doc:
            page_count = doc.page_count

        now = self._now()
        meta = ProjectMeta(
            id=project_id,
            title=title or Path(source_filename).stem,
            source_filename=source_filename,
            source_size_bytes=source_target.stat().st_size,
            page_count=page_count,
            created_at=now,
            updated_at=now,
            render_dpi=settings.render_dpi,
        )
        self.write_project(meta)
        (project_dir / "panels.json").write_text("{}", encoding="utf-8")
        return meta

    def write_project(self, meta: ProjectMeta) -> None:
        project_json = self._project_json(meta.id)
        project_json.write_text(json.dumps(meta.model_dump(mode="json"), indent=2), encoding="utf-8")

    def get_project(self, project_id: str) -> ProjectMeta:
        p = self._project_json(project_id)
        if not p.exists():
            raise FileNotFoundError("Project not found")
        return ProjectMeta.model_validate_json(p.read_text(encoding="utf-8"))

    def list_projects(self) -> list[ProjectListItem]:
        items: list[ProjectListItem] = []
        for pj in self.projects_dir.glob("*/project.json"):
            meta = ProjectMeta.model_validate_json(pj.read_text(encoding="utf-8"))
            items.append(
                ProjectListItem(
                    id=meta.id,
                    title=meta.title,
                    page_count=meta.page_count,
                    created_at=meta.created_at,
                    updated_at=meta.updated_at,
                    last_page_viewed=meta.last_page_viewed,
                    source_size_bytes=meta.source_size_bytes,
                    pages_detected_count=len(meta.pages_detected),
                    pages_edited_count=len(meta.pages_edited),
                    exported_at=meta.exported_at,
                )
            )
        items.sort(key=lambda x: x.updated_at, reverse=True)
        return items

    def update_title(self, project_id: str, title: str) -> ProjectMeta:
        meta = self.get_project(project_id)
        meta.title = title
        meta.updated_at = self._now()
        self.write_project(meta)
        return meta

    def delete_project(self, project_id: str) -> None:
        pdir = self._project_dir(project_id)
        if not pdir.exists():
            raise FileNotFoundError("Project not found")
        shutil.rmtree(pdir)

    def touch_project(self, project_id: str, **kwargs) -> ProjectMeta:
        meta = self.get_project(project_id)
        for key, val in kwargs.items():
            setattr(meta, key, val)
        meta.updated_at = self._now()
        self.write_project(meta)
        return meta

    def project_path(self, project_id: str) -> Path:
        pdir = self._project_dir(project_id)
        if not pdir.exists():
            raise FileNotFoundError("Project not found")
        return pdir
