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


def _build_top_block_page(path: Path) -> None:
    img = Image.new("L", (1000, 1400), color=255)
    draw = ImageDraw.Draw(img)

    # Large top paragraph-like block that should not be auto-excluded
    draw.rectangle((80, 40, 450, 420), fill=30)
    # lower block
    draw.rectangle((80, 520, 450, 900), fill=30)

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


def test_top_large_segment_not_excluded_and_is_padded(tmp_path: Path):
    image_path = tmp_path / "top-block.png"
    _build_top_block_page(image_path)

    detector = LayoutDetector()
    page = detector.detect(page_num=1, image_path=image_path)

    top_panel = min(page.panels, key=lambda p: p.y)
    assert top_panel.include is True
    assert top_panel.type == "text"

    # detector should pad beyond the raw rectangle bounds
    assert top_panel.y <= 35
    assert top_panel.height >= 390


def _build_order_and_footer_page(path: Path) -> None:
    img = Image.new("L", (1000, 1400), color=255)
    draw = ImageDraw.Draw(img)

    # Top row blocks: right starts slightly higher than left
    draw.rectangle((120, 80, 420, 260), fill=30)
    draw.rectangle((560, 60, 900, 260), fill=30)
    # Mid content
    draw.rectangle((560, 320, 900, 640), fill=30)
    # Footer strip near bottom that should be excluded
    draw.rectangle((80, 1320, 920, 1370), fill=30)

    img.save(path)


def test_ordering_prefers_left_to_right_on_same_row_and_excludes_footer(tmp_path: Path):
    image_path = tmp_path / "order-footer.png"
    _build_order_and_footer_page(image_path)

    detector = LayoutDetector()
    page = detector.detect(page_num=1, image_path=image_path)

    included = [p for p in page.panels if p.include]
    assert included

    first = min(included, key=lambda p: p.order)
    assert first.x < 500

    footer_like = [p for p in page.panels if p.y > 1250]
    assert footer_like
    assert all(not p.include for p in footer_like)


def _build_column_first_order_page(path: Path) -> None:
    img = Image.new("L", (1000, 1400), color=255)
    draw = ImageDraw.Draw(img)

    # Left column top and lower blocks
    draw.rectangle((80, 120, 430, 420), fill=30)
    draw.rectangle((80, 520, 430, 900), fill=30)

    # Right column starts slightly higher than left top block
    draw.rectangle((560, 80, 920, 360), fill=30)
    draw.rectangle((560, 460, 920, 800), fill=30)

    img.save(path)


def test_panel_ordering_is_column_first(tmp_path: Path):
    image_path = tmp_path / "column-first.png"
    _build_column_first_order_page(image_path)

    detector = LayoutDetector()
    page = detector.detect(page_num=1, image_path=image_path)

    included = sorted([p for p in page.panels if p.include], key=lambda p: p.order)
    assert len(included) >= 4

    # First two included panels should come from the left column.
    assert included[0].x < 500
    assert included[1].x < 500
