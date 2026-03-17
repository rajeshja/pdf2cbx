import logging
from pathlib import Path

from PIL import Image

from models.panel import PagePanels, Panel

logger = logging.getLogger(__name__)


class LayoutDetector:
    @staticmethod
    def _find_dense_runs(values: list[float], threshold: float, min_size: int) -> list[tuple[int, int]]:
        runs: list[tuple[int, int]] = []
        start = None
        for idx, value in enumerate(values):
            if value > threshold and start is None:
                start = idx
            elif value <= threshold and start is not None:
                if idx - start >= min_size:
                    runs.append((start, idx))
                start = None
        if start is not None and len(values) - start >= min_size:
            runs.append((start, len(values)))
        return runs

    @staticmethod
    def _merge_nearby_runs(runs: list[tuple[int, int]], gap: int) -> list[tuple[int, int]]:
        if not runs:
            return []
        merged = [runs[0]]
        for start, end in runs[1:]:
            prev_start, prev_end = merged[-1]
            if start - prev_end <= gap:
                merged[-1] = (prev_start, end)
            else:
                merged.append((start, end))
        return merged

    def detect(self, page_num: int, image_path: Path, confidence_threshold: float = 0.5, model: str = "opencv") -> PagePanels:
        with Image.open(image_path) as img:
            gray = img.convert("L")
            width, height = gray.size
            pix = gray.load()

            col_threshold = 0.02
            col_min_size = max(80, width // 12)
            col_merge_gap = max(16, width // 100)
            row_threshold = 0.02
            row_min_size = max(24, height // 80)
            row_merge_gap = max(16, height // 120)

            col_dark = []
            for x in range(width):
                dark = 0
                for y in range(height):
                    if pix[x, y] < 220:
                        dark += 1
                col_dark.append(dark / height)

            raw_columns = self._find_dense_runs(col_dark, threshold=col_threshold, min_size=col_min_size)
            columns = self._merge_nearby_runs(raw_columns, gap=col_merge_gap)
            if not columns:
                columns = [(0, width)]

            logger.info(
                "layout.detect page=%s size=%sx%s columns=%s raw_columns=%s model=%s conf=%.2f",
                page_num,
                width,
                height,
                len(columns),
                len(raw_columns),
                model,
                confidence_threshold,
            )
            logger.debug(
                "layout.detect.thresholds page=%s col_threshold=%.3f col_min=%s col_gap=%s row_threshold=%.3f row_min=%s row_gap=%s",
                page_num,
                col_threshold,
                col_min_size,
                col_merge_gap,
                row_threshold,
                row_min_size,
                row_merge_gap,
            )
            logger.debug("layout.detect.columns page=%s columns=%s", page_num, columns)

            panels: list[Panel] = []
            idx = 1
            for col_idx, (x1, x2) in enumerate(columns, start=1):
                col_width = x2 - x1
                if col_width < 50:
                    logger.debug("layout.detect.skip_column page=%s col=%s width=%s", page_num, col_idx, col_width)
                    continue

                row_dark = []
                for y in range(height):
                    dark = 0
                    for x in range(x1, x2):
                        if pix[x, y] < 220:
                            dark += 1
                    row_dark.append(dark / col_width)

                raw_segments = self._find_dense_runs(row_dark, threshold=row_threshold, min_size=row_min_size)
                segments = self._merge_nearby_runs(raw_segments, gap=row_merge_gap)
                logger.debug(
                    "layout.detect.segments page=%s col=%s x=%s-%s raw=%s merged=%s",
                    page_num,
                    col_idx,
                    x1,
                    x2,
                    len(raw_segments),
                    len(segments),
                )

                for y1, y2 in segments:
                    w = col_width
                    h = y2 - y1
                    if w < 50 or h < 50:
                        logger.debug("layout.detect.skip_segment page=%s col=%s box=(%s,%s,%s,%s)", page_num, col_idx, x1, y1, w, h)
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

            panels.sort(key=lambda p: (p.y, p.x))
            for order, panel in enumerate(panels, start=1):
                if panel.include:
                    panel.order = order
                    panel.label = f"Panel {order}"

            if not panels:
                logger.warning("layout.detect.no_panels page=%s fallback=full_page", page_num)
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

            logger.info("layout.detect.complete page=%s panels=%s", page_num, len(panels))
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
