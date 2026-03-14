# Data Model

## 1. File System Layout

All project data is stored under a configurable base directory (default: `~/pdf2cbz/projects/`).

```
~/pdf2cbz/
├── config.json                     # App-level settings
│
└── projects/
    └── {project_id}/               # UUID, e.g. 3f2a1b4c-...
        ├── project.json            # Project metadata
        ├── source.pdf              # Original uploaded PDF (read-only)
        ├── pages/                  # Cached rendered page images
        │   ├── 0001.jpg
        │   ├── 0002.jpg
        │   └── ...
        ├── panels.json             # All panel data for all pages
        ├── templates/              # Saved panel layout templates
        │   └── {template_id}.json
        └── output/
            └── {title}.cbz        # Exported CBZ (overwritten on re-export)
```

---

## 2. JSON Schemas

### 2.1 `config.json`

App-level configuration. Created on first run with defaults.

```json
{
  "projects_dir": "/home/user/pdf2cbz/projects",
  "render_dpi": 150,
  "default_jpeg_quality": 85,
  "max_undo_steps": 20,
  "detection_model": "surya",
  "detection_confidence_threshold": 0.5
}
```

| Field | Type | Description |
|---|---|---|
| `projects_dir` | string | Absolute path to projects root |
| `render_dpi` | integer | DPI for page rendering (100–300) |
| `default_jpeg_quality` | integer | JPEG quality for export (1–100) |
| `max_undo_steps` | integer | Undo history depth per page |
| `detection_model` | string | `"surya"` or `"opencv"` |
| `detection_confidence_threshold` | float | Min confidence for surya detections (0–1) |

---

### 2.2 `project.json`

Project metadata. Written on import, updated on export.

```json
{
  "id": "3f2a1b4c-9d2e-4f1a-b3c5-7a8e2f0d1b6c",
  "title": "The Art of War",
  "source_filename": "art_of_war_scan.pdf",
  "source_size_bytes": 214748364,
  "page_count": 312,
  "created_at": "2025-03-14T10:22:00Z",
  "updated_at": "2025-03-14T11:45:00Z",
  "last_page_viewed": 42,
  "render_dpi": 150,
  "exported_at": null,
  "export_filename": null,
  "pages_detected": [1, 2, 3, 42],
  "pages_edited": [2, 42]
}
```

| Field | Type | Description |
|---|---|---|
| `id` | string (UUID) | Unique project identifier |
| `title` | string | Display name (derived from filename, editable) |
| `source_filename` | string | Original filename as uploaded |
| `source_size_bytes` | integer | PDF file size |
| `page_count` | integer | Total pages in PDF |
| `created_at` | ISO 8601 datetime | Import timestamp |
| `updated_at` | ISO 8601 datetime | Last edit timestamp |
| `last_page_viewed` | integer | 1-based page number for resume |
| `render_dpi` | integer | DPI used for this project's page renders |
| `exported_at` | ISO 8601 datetime or null | Last export timestamp |
| `export_filename` | string or null | Output CBZ filename |
| `pages_detected` | integer[] | Pages where detection has been run |
| `pages_edited` | integer[] | Pages where panels have been manually edited |

---

### 2.3 `panels.json`

Stores all panel data for all pages in the project. Keyed by page number (1-based, as strings for JSON compatibility).

```json
{
  "1": {
    "page": 1,
    "source_width": 1654,
    "source_height": 2339,
    "detection_run": true,
    "detection_model": "surya",
    "detection_confidence_threshold": 0.5,
    "manually_edited": false,
    "panels": [
      {
        "id": "p1-001",
        "order": 1,
        "x": 112,
        "y": 148,
        "width": 680,
        "height": 890,
        "type": "text",
        "include": true,
        "confidence": 0.92,
        "label": "Column 1"
      },
      {
        "id": "p1-002",
        "order": 2,
        "x": 862,
        "y": 148,
        "width": 680,
        "height": 890,
        "type": "text",
        "include": true,
        "confidence": 0.89,
        "label": "Column 2"
      },
      {
        "id": "p1-003",
        "order": 0,
        "x": 0,
        "y": 0,
        "width": 1654,
        "height": 120,
        "type": "header",
        "include": false,
        "confidence": 0.95,
        "label": "Header"
      }
    ]
  },
  "2": { ... }
}
```

#### Panel Object

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique panel ID, format `p{page}-{seq}` |
| `order` | integer | Reading order (1-based). 0 = excluded from output |
| `x` | integer | Left edge in pixels (relative to rendered page image) |
| `y` | integer | Top edge in pixels |
| `width` | integer | Width in pixels |
| `height` | integer | Height in pixels |
| `type` | string | `text`, `figure`, `table`, `header`, `footer`, `unknown` |
| `include` | boolean | Whether to include in CBZ export |
| `confidence` | float (0–1) | Detection confidence (1.0 for manually added panels) |
| `label` | string | Human-readable label shown in panel list |

---

### 2.4 Template `{template_id}.json`

A saved panel layout that can be applied to other pages. Coordinates are stored as percentages of page dimensions to allow application across pages with slightly different rendered sizes.

```json
{
  "id": "tmpl-a1b2c3",
  "name": "Standard 2-column body page",
  "created_from_page": 5,
  "created_at": "2025-03-14T11:00:00Z",
  "panels": [
    {
      "order": 1,
      "x_pct": 0.068,
      "y_pct": 0.063,
      "width_pct": 0.411,
      "height_pct": 0.381,
      "type": "text",
      "include": true,
      "label": "Column 1"
    }
  ]
}
```

---

## 3. CBZ Output Structure

A CBZ file is a ZIP archive. Panel images are named to sort lexicographically in reading order.

```
{title}.cbz
├── ComicInfo.xml
├── pdf2cbz_page_0001_panel_001.jpg
├── pdf2cbz_page_0001_panel_002.jpg
├── pdf2cbz_page_0001_panel_003.jpg
├── pdf2cbz_page_0002_panel_001.jpg
└── ...
```

### Filename Format

```
pdf2cbz_page_{PPPP}_panel_{NNN}.jpg
```

- `PPPP` — zero-padded 4-digit page number
- `NNN` — zero-padded 3-digit panel reading order within the page

### `ComicInfo.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<ComicInfo xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <Title>The Art of War</Title>
  <Notes>Converted from PDF scan by PDF2CBZ</Notes>
  <PageCount>312</PageCount>
</ComicInfo>
```

---

## 4. In-Memory State (Frontend)

The frontend maintains an undo/redo stack per page in Zustand. This is ephemeral — it is not persisted to the backend and resets on page navigation.

```typescript
interface PanelState {
  panels: Panel[];
  undoStack: Panel[][];   // previous states
  redoStack: Panel[][];   // future states (after undo)
}

interface Panel {
  id: string;
  order: number;
  x: number;
  y: number;
  width: number;
  height: number;
  type: PanelType;
  include: boolean;
  confidence: number;
  label: string;
}

type PanelType = 'text' | 'figure' | 'table' | 'header' | 'footer' | 'unknown';
```
