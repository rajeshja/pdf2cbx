# Pipeline Design

## 1. Overview

The processing pipeline has three stages: **PDF Rendering**, **Layout Detection**, and **CBZ Export**. Each stage is designed to be lazy (process on demand), resumable (cache results), and non-blocking (run in background threads).

---

## 2. PDF Rendering Pipeline

### 2.1 Library: PyMuPDF (fitz)

PyMuPDF is the best choice for this use case:
- Fast per-page rendering with low memory overhead
- Handles large scanned PDFs without loading all pages into memory
- Supports DPI-controlled rendering
- Returns page dimensions, enabling coordinate mapping

### 2.2 Rendering Process

```python
import fitz  # PyMuPDF

def render_page(pdf_path: str, page_num: int, dpi: int = 150) -> tuple[bytes, int, int]:
    """
    Render a single PDF page to JPEG bytes.
    Returns (jpeg_bytes, width_px, height_px).
    Page num is 0-based internally, converted from 1-based API input.
    """
    doc = fitz.open(pdf_path)
    page = doc[page_num - 1]  # 0-based index

    # Scale matrix for target DPI (PDF internal unit = 72 DPI)
    scale = dpi / 72.0
    matrix = fitz.Matrix(scale, scale)

    pixmap = page.get_pixmap(matrix=matrix, colorspace=fitz.csRGB)
    jpeg_bytes = pixmap.tobytes("jpeg", jpg_quality=92)

    return jpeg_bytes, pixmap.width, pixmap.height
```

### 2.3 Caching Strategy

- Pages are cached as JPEG files: `projects/{id}/pages/{NNNN}.jpg`
- Cache key: `(project_id, page_num, dpi)`
- Cache is checked before rendering; render only on miss
- Cache is invalidated manually (user action) or if DPI setting changes
- No LRU eviction — disk space warning shown at < 500MB free

### 2.4 DPI Selection

| DPI | Width (typical A4 page) | JPEG size | Notes |
|---|---|---|---|
| 100 | ~827px | ~150 KB | Acceptable for small phones |
| 150 | ~1240px | ~300 KB | **Default — good balance** |
| 200 | ~1654px | ~500 KB | Better for fine text / figures |
| 300 | ~2480px | ~1.1 MB | High quality, slow on large books |

150 DPI is the default. At 150 DPI, a 312-page book with ~300 KB/page = ~90 MB cached pages.

---

## 3. Layout Detection Pipeline

### 3.1 Primary Model: surya

[surya](https://github.com/VikParuchuri/surya) is an open-source document layout analysis model. It detects text blocks, figures, tables, headers, and footers with high accuracy on scanned documents without any fine-tuning.

**Detection flow:**

```
Page JPEG
    │
    ▼
surya layout model
    │
    ▼
List of LayoutBox objects:
    { bbox: [x1,y1,x2,y2], label: "Text"|"Figure"|"Table"|"Header"|"Footer", confidence: float }
    │
    ▼
Convert to panel format:
    { x, y, width, height, type, confidence }
    │
    ▼
Post-processing (see 3.3)
    │
    ▼
Save to panels.json
```

**Python sketch:**

```python
from surya.layout import batch_layout_detection
from surya.model.layout.encoderdecoder import LayoutEncoderDecoder
from PIL import Image

model = LayoutEncoderDecoder.from_pretrained("vikp/surya_layout3")

def detect_layout(image_path: str, confidence_threshold: float = 0.5) -> list[dict]:
    image = Image.open(image_path).convert("RGB")
    results = batch_layout_detection([image], model, [None])
    
    panels = []
    for box in results[0].bboxes:
        if box.confidence < confidence_threshold:
            continue
        x1, y1, x2, y2 = box.bbox
        panels.append({
            "x": int(x1), "y": int(y1),
            "width": int(x2 - x1), "height": int(y2 - y1),
            "type": box.label.lower(),
            "confidence": round(box.confidence, 3)
        })
    return panels
```

### 3.2 Fallback: OpenCV Contour Detection

For simpler pages or when surya gives poor results, a lightweight OpenCV-based detector is available.

```
Page JPEG
    │
    ▼
Convert to grayscale
    │
    ▼
Adaptive threshold (binarise)
    │
    ▼
Morphological close (horizontal kernel) → merge characters into lines
    │
    ▼
Morphological close (vertical kernel) → merge lines into paragraphs
    │
    ▼
Find contours
    │
    ▼
Filter by area (remove noise, page borders)
    │
    ▼
Merge overlapping boxes (IoU threshold 0.3)
    │
    ▼
Return bounding boxes
```

The OpenCV detector is faster but less accurate — it won't distinguish text from figures, and struggles with complex layouts.

### 3.3 Post-Processing

After detection (either model), the following steps are applied:

**1. Coordinate clipping**
Clip all boxes to page bounds. surya occasionally returns boxes slightly outside the page.

**2. Noise filtering**
Remove boxes smaller than 50×20px (likely single characters or artifacts).

**3. Overlap deduplication**
When two boxes overlap by > 60% IoU, keep the higher-confidence one.

**4. Column sorting (reading order)**
Sort panels into reading order:
- For single-column pages: top to bottom
- For multi-column pages: detect column centres, then sort left-column top-to-bottom, then right-column top-to-bottom
- Column detection: cluster `x_centre` values; if two clear clusters exist, treat as two-column

**5. Header/footer exclusion**
Boxes with `type == "header"` or `"footer"` have `include = false` by default. Boxes in the top 8% or bottom 8% of the page with any type are also flagged for review.

**6. Order assignment**
Assign `order` values (1, 2, 3...) to included panels in reading order. Excluded panels get `order = 0`.

---

## 4. CBZ Export Pipeline

### 4.1 Process

```
For each page P in [page_from .. page_to]:
    1. Load panels for page P (panels.json)
    2. Filter: keep panels where include=true, ordered by order asc
    3. Render page P if not cached (or use cache)
    4. Open page image with Pillow
    5. For each panel in order:
           crop = image.crop((x, y, x+w, y+h))
           encode to JPEG at requested quality
           write to ZIP as "pdf2cbz_page_{P:04d}_panel_{N:03d}.jpg"
    6. Release page image from memory

After all pages:
    Write ComicInfo.xml to ZIP
    Close ZIP
```

### 4.2 Memory Management

The critical constraint is 300MB PDFs. The export pipeline never holds more than one page image in memory at a time:

```python
import zipfile
from PIL import Image
import io

def export_cbz(project, output_path, quality=85, page_from=1, page_to=None):
    if page_to is None:
        page_to = project.page_count

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_STORED) as zf:
        panel_counter = 0

        for page_num in range(page_from, page_to + 1):
            page_panels = get_included_panels(project, page_num)
            if not page_panels:
                continue

            # Load page image — released at end of loop iteration
            with Image.open(get_page_image_path(project, page_num)) as page_img:
                for panel in sorted(page_panels, key=lambda p: p['order']):
                    x, y, w, h = panel['x'], panel['y'], panel['width'], panel['height']
                    crop = page_img.crop((x, y, x + w, y + h))

                    buf = io.BytesIO()
                    crop.save(buf, format='JPEG', quality=quality)
                    buf.seek(0)

                    filename = f"pdf2cbz_page_{page_num:04d}_panel_{panel['order']:03d}.jpg"
                    zf.writestr(filename, buf.read())
                    panel_counter += 1

                    yield page_num, panel_counter  # for progress reporting

        zf.writestr("ComicInfo.xml", build_comic_info_xml(project))
```

### 4.3 Progress Reporting

Export runs as a background task. Progress is reported as a fraction:

```
progress = pages_completed / total_pages
```

The frontend polls `GET /api/tasks/{task_id}` every 2 seconds and updates a progress bar.

### 4.4 ZIP Compression

CBZ files use `ZIP_STORED` (no compression) for the image files. JPEG is already compressed — applying ZIP DEFLATE to JPEGs wastes CPU for near-zero size savings. The `ComicInfo.xml` uses `ZIP_DEFLATED`.

---

## 5. Performance Benchmarks (Target)

Tested on a mid-range desktop (Intel i7, 16GB RAM, SSD):

| Operation | Target | Notes |
|---|---|---|
| Render one page at 150 DPI | < 2s | PyMuPDF is very fast |
| surya detection on one page | 5–15s | Depends on page complexity |
| OpenCV detection on one page | < 0.5s | Fast but less accurate |
| Export one panel to JPEG | < 50ms | Pillow crop + encode |
| Export 300-page book (3 panels/page) | < 10 min | ~900 panels total |

### Optimisation Notes

- **Surya batching:** surya can process multiple page images in a batch. Pre-render 4–8 pages and batch-detect to improve GPU/CPU utilisation
- **Page pre-rendering:** While the user edits page N, pre-render pages N+1 and N+2 in the background
- **Export parallelism:** Panel cropping and JPEG encoding can be parallelised across cores using `concurrent.futures.ProcessPoolExecutor`, but ZIP writing must remain sequential

---

## 6. Error Handling

| Error | Behaviour |
|---|---|
| PDF page is blank or corrupt | Skip detection, return empty panel list with warning flag |
| surya model fails to load | Fall back to OpenCV detector automatically |
| Disk full during export | Abort export, delete partial CBZ, return error to UI |
| Panel box outside page bounds | Clip to page bounds before cropping |
| Zero-dimension panel (width or height = 0) | Skip panel with warning, do not crash |
