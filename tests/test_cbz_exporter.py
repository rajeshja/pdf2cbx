from pathlib import Path
from zipfile import ZipFile

from PIL import Image

from core.cbz_exporter import CBZExporter
from core.panel_store import PanelStore
from models.panel import Panel
from models.project import ProjectMeta
from models.task import TaskStatus


def _seed_project(project_dir: Path) -> ProjectMeta:
    (project_dir / "pages").mkdir(parents=True)
    (project_dir / "output").mkdir(parents=True)
    (project_dir / "source.pdf").write_bytes(b"%PDF-1.4\n")

    image_path = project_dir / "pages" / "0001.jpg"
    Image.new("RGB", (1200, 1800), color=(220, 220, 220)).save(image_path)

    store = PanelStore(project_dir)
    store.save_from_panels(
        page_num=1,
        source_width=1200,
        source_height=1800,
        panels=[
            Panel(order=1, x=100, y=100, width=400, height=500, label="A"),
            Panel(order=2, x=600, y=300, width=450, height=600, label="B"),
        ],
    )

    return ProjectMeta(
        id="proj-1",
        title="Book",
        source_filename="source.pdf",
        source_size_bytes=10,
        page_count=1,
    )


def test_export_defaults_to_page_images_and_panel_map(tmp_path: Path):
    project = _seed_project(tmp_path)
    exporter = CBZExporter()
    task = TaskStatus(id="t1", type="export")

    result = exporter.export(project, tmp_path, jpeg_quality=85, page_from=1, page_to=1, task=task)

    assert result["output_filename"].endswith(".cbz")
    assert result["panel_count"] == 0
    assert result["page_image_count"] == 1

    with ZipFile(tmp_path / "output" / result["output_filename"]) as zf:
        names = set(zf.namelist())
        assert "pdf2cbz_page_0001.jpg" in names
        assert "PanelMap.json" in names
        assert "ComicInfo.xml" in names
        assert "pdf2cbz_page_0001_panel_001.jpg" not in names


def test_export_cbx_can_include_panel_crops(tmp_path: Path):
    project = _seed_project(tmp_path)
    exporter = CBZExporter()
    task = TaskStatus(id="t2", type="export")

    result = exporter.export(
        project,
        tmp_path,
        jpeg_quality=85,
        page_from=1,
        page_to=1,
        task=task,
        archive_format="cbx",
        include_panel_images=True,
    )

    assert result["output_filename"].endswith(".cbx")
    assert result["panel_count"] == 2

    with ZipFile(tmp_path / "output" / result["output_filename"]) as zf:
        names = set(zf.namelist())
        assert "pdf2cbz_page_0001_panel_001.jpg" in names
        assert "pdf2cbz_page_0001_panel_002.jpg" in names
