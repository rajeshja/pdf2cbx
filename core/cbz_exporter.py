from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from PIL import Image

from core.panel_store import PanelStore
from core.pdf_renderer import PDFRenderer
from models.project import ProjectMeta
from models.task import TaskStatus


class CBZExporter:
    def __init__(self):
        self.renderer = PDFRenderer()

    def export(
        self,
        project: ProjectMeta,
        project_dir: Path,
        jpeg_quality: int,
        page_from: int,
        page_to: int,
        task: TaskStatus,
    ) -> dict:
        output_dir = project_dir / "output"
        output_dir.mkdir(exist_ok=True)
        out_file = output_dir / f"{project.title}.cbz"
        source_pdf = project_dir / "source.pdf"
        page_total = max(1, page_to - page_from + 1)
        panel_store = PanelStore(project_dir)
        panel_count = 0

        with ZipFile(out_file, "w", compression=ZIP_DEFLATED) as zf:
            for idx, page_num in enumerate(range(page_from, page_to + 1), start=1):
                task.progress = idx / page_total
                task.progress_label = f"Page {page_num} of {page_to}"
                cache_path = project_dir / "pages" / f"{page_num:04d}.jpg"
                if not cache_path.exists():
                    self.renderer.render_page(source_pdf, page_num, project.render_dpi, cache_path)

                with Image.open(cache_path) as page_img:
                    page_panels = panel_store.get_page(page_num)
                    if page_panels is None:
                        continue
                    included = [p for p in page_panels.panels if p.include and p.order > 0]
                    included.sort(key=lambda p: p.order)
                    for panel in included:
                        box = (
                            max(0, panel.x),
                            max(0, panel.y),
                            min(page_img.width, panel.x + panel.width),
                            min(page_img.height, panel.y + panel.height),
                        )
                        cropped = page_img.crop(box)
                        data = BytesIO()
                        cropped.save(data, format="JPEG", quality=jpeg_quality)
                        zf.writestr(f"pdf2cbz_page_{page_num:04d}_panel_{panel.order:03d}.jpg", data.getvalue())
                        panel_count += 1

            comic_info = (
                "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n"
                "<ComicInfo xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\">\n"
                f"  <Title>{project.title}</Title>\n"
                "  <Notes>Converted from PDF scan by PDF2CBZ</Notes>\n"
                f"  <PageCount>{page_to - page_from + 1}</PageCount>\n"
                "</ComicInfo>\n"
            )
            zf.writestr("ComicInfo.xml", comic_info)

        return {
            "output_filename": out_file.name,
            "panel_count": panel_count,
            "file_size_bytes": out_file.stat().st_size,
        }
