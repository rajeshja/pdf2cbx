from pathlib import Path

from PIL import Image

from models.panel import PagePanels, Panel


class LayoutDetector:
    def detect(self, page_num: int, image_path: Path, confidence_threshold: float = 0.5, model: str = "opencv") -> PagePanels:
        with Image.open(image_path) as img:
            gray = img.convert("L")
            width, height = gray.size
            pix = gray.load()

            row_dark = []
            for y in range(height):
                dark = 0
                for x in range(width):
                    if pix[x, y] < 220:
                        dark += 1
                row_dark.append(dark / width)

            segments: list[tuple[int, int]] = []
            start = None
            for y, ratio in enumerate(row_dark):
                if ratio > 0.02 and start is None:
                    start = y
                elif ratio <= 0.02 and start is not None:
                    if y - start > 30:
                        segments.append((start, y))
                    start = None
            if start is not None:
                segments.append((start, height))

            panels: list[Panel] = []
            idx = 1
            for y1, y2 in segments:
                col_density = []
                for x in range(width):
                    dark = 0
                    for y in range(y1, y2):
                        if pix[x, y] < 220:
                            dark += 1
                    col_density.append(dark / max(1, (y2 - y1)))

                valleys = [x for x, v in enumerate(col_density) if v < 0.01]
                split = None
                if valleys:
                    mid = width // 2
                    nearest = min(valleys, key=lambda v: abs(v - mid))
                    if abs(nearest - mid) < width * 0.2:
                        split = nearest

                if split:
                    candidates = [(0, split), (split, width)]
                else:
                    candidates = [(0, width)]

                for x1, x2 in candidates:
                    w = x2 - x1
                    h = y2 - y1
                    if w < 50 or h < 50:
                        continue
                    ptype = "header" if y1 < int(height * 0.08) else "footer" if y2 > int(height * 0.92) else "text"
                    include = ptype not in {"header", "footer"}
                    panels.append(
                        Panel(
                            id=f"p{page_num}-{idx:03d}",
                            order=idx if include else 0,
                            x=x1,
                            y=y1,
                            width=w,
                            height=h,
                            type=ptype,
                            include=include,
                            confidence=max(confidence_threshold, 0.7),
                            label=f"Panel {idx}",
                        )
                    )
                    idx += 1

            if not panels:
                panels = [
                    Panel(
                        id=f"p{page_num}-001",
                        order=1,
                        x=0,
                        y=0,
                        width=width,
                        height=height,
                        type="unknown",
                        include=True,
                        confidence=1.0,
                        label="Full page",
                    )
                ]

            return PagePanels(
                page=page_num,
                source_width=width,
                source_height=height,
                detection_run=True,
                detection_model=model,
                detection_confidence_threshold=confidence_threshold,
                manually_edited=False,
                panels=panels,
            )
