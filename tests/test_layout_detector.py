from pathlib import Path

from PIL import Image, ImageDraw

from core.layout_detector import LayoutDetector


def _build_two_column_page(path: Path) -> None:
    img = Image.new("L", (1000, 1400), color=255)
    draw = ImageDraw.Draw(img)

    # Left column paragraphs
    draw.rectangle((80, 100, 450, 340), fill=30)
    draw.rectangle((80, 420, 450, 760), fill=30)

    # Right column paragraphs
    draw.rectangle((560, 140, 920, 360), fill=30)
    draw.rectangle((560, 460, 920, 820), fill=30)

    img.save(path)


def test_detect_splits_two_column_layout(tmp_path: Path):
    image_path = tmp_path / "two-column.png"
    _build_two_column_page(image_path)

    detector = LayoutDetector()
    page = detector.detect(page_num=1, image_path=image_path)

    text_panels = [p for p in page.panels if p.type == "text"]
    assert len(text_panels) >= 4

    left_column = [p for p in text_panels if p.x < 500]
    right_column = [p for p in text_panels if p.x >= 500]

    assert left_column and right_column
    assert all(panel.width < 500 for panel in text_panels)
