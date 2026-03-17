import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from models.panel import PagePanels, Panel


class PanelStore:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.panels_path = project_dir / "panels.json"
        if not self.panels_path.exists():
            self.panels_path.write_text("{}", encoding="utf-8")

    def _load(self) -> dict:
        return json.loads(self.panels_path.read_text(encoding="utf-8"))

    def _save(self, data: dict):
        tmp = self.panels_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp.replace(self.panels_path)

    def get_page(self, page_num: int) -> PagePanels | None:
        data = self._load()
        obj = data.get(str(page_num))
        return PagePanels.model_validate(obj) if obj else None

    def save_page(self, page: PagePanels) -> PagePanels:
        for i, p in enumerate(page.panels, start=1):
            if not p.id:
                p.id = f"p{page.page}-{i:03d}"
        data = self._load()
        data[str(page.page)] = page.model_dump(mode="json")
        self._save(data)
        return page

    def save_from_panels(self, page_num: int, source_width: int, source_height: int, panels: list[Panel], model: str = "manual") -> PagePanels:
        normalized: list[Panel] = []
        for i, panel in enumerate(panels, start=1):
            normalized.append(
                Panel(
                    id=panel.id or f"p{page_num}-{i:03d}",
                    order=panel.order,
                    x=panel.x,
                    y=panel.y,
                    width=panel.width,
                    height=panel.height,
                    type=panel.type,
                    include=panel.include,
                    confidence=panel.confidence if panel.confidence is not None else 1.0,
                    label=panel.label,
                )
            )
        page = PagePanels(
            page=page_num,
            source_width=source_width,
            source_height=source_height,
            detection_run=True,
            detection_model=model,
            manually_edited=True,
            panels=normalized,
        )
        return self.save_page(page)

    def create_template(self, source_page: int, name: str, panels: list[Panel], source_width: int, source_height: int) -> dict:
        template_id = f"tmpl-{uuid.uuid4().hex[:6]}"
        payload = {
            "id": template_id,
            "name": name,
            "created_from_page": source_page,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "panels": [
                {
                    "order": p.order,
                    "x_pct": p.x / source_width,
                    "y_pct": p.y / source_height,
                    "width_pct": p.width / source_width,
                    "height_pct": p.height / source_height,
                    "type": p.type,
                    "include": p.include,
                    "label": p.label,
                }
                for p in panels
            ],
        }
        tpath = self.project_dir / "templates" / f"{template_id}.json"
        tpath.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return {"id": template_id, "name": name, "panel_count": len(panels)}

    def apply_template(self, template_id: str, page_num: int, source_width: int, source_height: int) -> PagePanels:
        tpath = self.project_dir / "templates" / f"{template_id}.json"
        tpl = json.loads(tpath.read_text(encoding="utf-8"))
        panels: list[Panel] = []
        for i, tp in enumerate(tpl["panels"], start=1):
            panels.append(
                Panel(
                    id=f"p{page_num}-{i:03d}",
                    order=tp["order"],
                    x=int(tp["x_pct"] * source_width),
                    y=int(tp["y_pct"] * source_height),
                    width=int(tp["width_pct"] * source_width),
                    height=int(tp["height_pct"] * source_height),
                    type=tp["type"],
                    include=tp["include"],
                    confidence=1.0,
                    label=tp.get("label", f"Panel {i}"),
                )
            )
        page = PagePanels(
            page=page_num,
            source_width=source_width,
            source_height=source_height,
            detection_run=True,
            detection_model="template",
            manually_edited=True,
            panels=panels,
        )
        return self.save_page(page)
