from io import BytesIO
from pathlib import Path

import fitz
from PIL import Image


class PDFRenderer:
    def render_page(self, pdf_path: Path, page_num: int, dpi: int, out_path: Path | None = None) -> tuple[bytes, int, int]:
        with fitz.open(pdf_path) as doc:
            if page_num < 1 or page_num > doc.page_count:
                raise IndexError("Page number out of range")
            page = doc.load_page(page_num - 1)
            matrix = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=90)
            data = buf.getvalue()
            if out_path:
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(data)
            return data, pix.width, pix.height

    def thumbnail(self, image_path: Path, width: int = 150) -> bytes:
        with Image.open(image_path) as img:
            ratio = width / img.width
            h = max(1, int(img.height * ratio))
            thumb = img.resize((width, h))
            buf = BytesIO()
            thumb.save(buf, format="JPEG", quality=80)
            return buf.getvalue()
