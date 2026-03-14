# API Reference

All endpoints are served by the FastAPI backend at `http://localhost:8000/api`.

Interactive docs available at `http://localhost:8000/docs` (Swagger UI) and `http://localhost:8000/redoc`.

---

## Conventions

- All request/response bodies are JSON unless otherwise noted
- Page numbers are **1-based** throughout
- Coordinates (`x`, `y`, `width`, `height`) are in **pixels** relative to the rendered page image at the project's configured DPI
- Timestamps are ISO 8601 in UTC
- Errors follow the format: `{ "detail": "Human-readable message" }`

---

## Projects

### `GET /api/projects`

List all projects.

**Response `200`**
```json
[
  {
    "id": "3f2a1b4c-...",
    "title": "The Art of War",
    "page_count": 312,
    "created_at": "2025-03-14T10:22:00Z",
    "updated_at": "2025-03-14T11:45:00Z",
    "last_page_viewed": 42,
    "source_size_bytes": 214748364,
    "pages_detected_count": 4,
    "pages_edited_count": 2,
    "exported_at": null
  }
]
```

---

### `POST /api/projects`

Import a new PDF and create a project. Streams the upload to disk.

**Request** `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | file | Yes | PDF file (max 300MB) |
| `title` | string | No | Display name. Defaults to filename without extension |

**Response `201`**
```json
{
  "id": "3f2a1b4c-...",
  "title": "The Art of War",
  "page_count": 312,
  "created_at": "2025-03-14T10:22:00Z"
}
```

**Errors**
- `400` — File is not a valid PDF
- `413` — File exceeds 300MB limit
- `507` — Insufficient disk space

---

### `GET /api/projects/{project_id}`

Get full project metadata.

**Response `200`** — Full `project.json` contents (see Data Model)

**Errors**
- `404` — Project not found

---

### `PATCH /api/projects/{project_id}`

Update project metadata (title only in v1).

**Request body**
```json
{ "title": "New Title" }
```

**Response `200`** — Updated project object

---

### `DELETE /api/projects/{project_id}`

Delete a project and all associated files including the source PDF.

**Response `204`** — No content

---

## Pages

### `GET /api/projects/{project_id}/pages/{page_num}/image`

Get a rendered JPEG image of a page. Renders and caches on first call.

**Path params**
- `page_num` — 1-based page number

**Query params**

| Param | Type | Default | Description |
|---|---|---|---|
| `dpi` | integer | project default | Override render DPI (100–300) |

**Response `200`**
- Content-Type: `image/jpeg`
- Body: JPEG binary
- Headers: `X-Page-Width`, `X-Page-Height` (pixel dimensions)

**Response `202`** — Rendering in progress (poll again)

**Errors**
- `404` — Page number out of range

---

### `GET /api/projects/{project_id}/pages/{page_num}/thumbnail`

Get a small thumbnail (150px wide) of a page. Used by the page strip navigator.

**Response `200`** — JPEG binary (Content-Type: `image/jpeg`)

---

## Panels

### `GET /api/projects/{project_id}/pages/{page_num}/panels`

Get panels for a page. Runs detection automatically if panels don't exist yet.

**Response `200`**
```json
{
  "page": 5,
  "source_width": 1654,
  "source_height": 2339,
  "detection_run": true,
  "detection_model": "surya",
  "manually_edited": false,
  "panels": [
    {
      "id": "p5-001",
      "order": 1,
      "x": 112,
      "y": 148,
      "width": 680,
      "height": 890,
      "type": "text",
      "include": true,
      "confidence": 0.92,
      "label": "Column 1"
    }
  ]
}
```

**Response `202`** — Detection in progress, poll again

---

### `PUT /api/projects/{project_id}/pages/{page_num}/panels`

Replace the full panel list for a page. Called by the frontend after any edit.

**Request body** — Array of panel objects (same schema as above, `id` and `confidence` optional for new panels)

```json
[
  {
    "id": "p5-001",
    "order": 1,
    "x": 120,
    "y": 150,
    "width": 675,
    "height": 885,
    "type": "text",
    "include": true,
    "label": "Column 1"
  }
]
```

**Response `200`** — Saved panel list (with assigned IDs for any new panels)

---

### `POST /api/projects/{project_id}/pages/{page_num}/detect`

Trigger or re-trigger layout detection, overwriting any saved panels.

**Request body**
```json
{
  "confidence_threshold": 0.4,
  "model": "surya"
}
```

**Response `202`**
```json
{ "task_id": "det-abc123", "status": "running" }
```

Poll `GET /api/tasks/{task_id}` for completion, then fetch panels again.

---

### `POST /api/projects/{project_id}/templates`

Save the current panel layout for a page as a reusable template.

**Request body**
```json
{
  "source_page": 5,
  "name": "Standard 2-column body page"
}
```

**Response `201`**
```json
{
  "id": "tmpl-a1b2c3",
  "name": "Standard 2-column body page",
  "panel_count": 3
}
```

---

### `POST /api/projects/{project_id}/templates/{template_id}/apply`

Apply a saved template to a range of pages.

**Request body**
```json
{
  "page_from": 10,
  "page_to": 50,
  "overwrite_edited": false
}
```

**Response `200`**
```json
{
  "applied_to": [10, 11, 12, 14, 15],
  "skipped": [13]
}
```

`skipped` pages are those that were manually edited and `overwrite_edited` was false.

---

## Export

### `POST /api/projects/{project_id}/export`

Start a CBZ export job.

**Request body**
```json
{
  "jpeg_quality": 85,
  "page_from": 1,
  "page_to": 312
}
```

| Field | Type | Default | Description |
|---|---|---|---|
| `jpeg_quality` | integer | 85 | JPEG compression quality (1–100) |
| `page_from` | integer | 1 | First page to include (1-based) |
| `page_to` | integer | last page | Last page to include (inclusive) |

**Response `202`**
```json
{ "task_id": "exp-xyz789", "status": "running" }
```

---

### `GET /api/projects/{project_id}/export/download`

Download the most recently exported CBZ file.

**Response `200`**
- Content-Type: `application/zip`
- Content-Disposition: `attachment; filename="The Art of War.cbz"`
- Body: CBZ binary

**Errors**
- `404` — No export has been completed for this project

---

## Background Tasks

### `GET /api/tasks/{task_id}`

Poll the status of a background task (detection or export).

**Response `200`**
```json
{
  "id": "exp-xyz789",
  "type": "export",
  "status": "running",
  "progress": 0.42,
  "progress_label": "Page 132 of 312",
  "started_at": "2025-03-14T11:50:00Z",
  "completed_at": null,
  "error": null
}
```

| Field | Values |
|---|---|
| `status` | `queued`, `running`, `complete`, `error` |
| `progress` | Float 0–1 |
| `error` | Error message string, or null |

**Response `200`** when complete:
```json
{
  "status": "complete",
  "progress": 1.0,
  "completed_at": "2025-03-14T11:53:22Z",
  "result": {
    "output_filename": "The Art of War.cbz",
    "panel_count": 847,
    "file_size_bytes": 52428800
  }
}
```

---

## Settings

### `GET /api/settings`

Get current app configuration.

**Response `200`** — `config.json` contents

---

### `PATCH /api/settings`

Update app configuration.

**Request body** — Partial config object (only include fields to change)

**Response `200`** — Updated full config

---

### `DELETE /api/cache`

Clear all cached page render images across all projects.

**Response `200`**
```json
{ "deleted_files": 1247, "freed_bytes": 524288000 }
```
