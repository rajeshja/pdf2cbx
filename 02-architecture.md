# Architecture

## 1. System Overview

PDF2CBZ is a single-machine application consisting of a Python backend and a React frontend. The backend serves both the API and the compiled frontend as static files, so only one process needs to run.

```
┌─────────────────────────────────────────────────────────────┐
│                        User's PC                            │
│                                                             │
│  ┌──────────────┐        ┌──────────────────────────────┐  │
│  │   FastAPI    │        │        File System           │  │
│  │   Backend    │◄──────►│  ~/pdf2cbz/projects/         │  │
│  │  :8000       │        │    <project>/                │  │
│  │              │        │      pages/    (cached imgs) │  │
│  │  + Static    │        │      panels.json             │  │
│  │    Files     │        │      source.pdf              │  │
│  │  (React PWA) │        │      output.cbz              │  │
│  └──────┬───────┘        └──────────────────────────────┘  │
│         │                                                   │
└─────────┼───────────────────────────────────────────────────┘
          │ HTTP / WebSocket
          │
    ┌─────┴──────────────────────────┐
    │  (optional) Cloudflare Tunnel  │
    └─────┬──────────────────────────┘
          │ HTTPS
          │
    ┌─────┴──────────┐
    │  Android/Web   │
    │  Browser       │
    │  (PWA)         │
    └────────────────┘
```

---

## 2. Component Architecture

### 2.1 Backend Components

```
app.py                          # FastAPI entry point
│
├── routers/
│   ├── projects.py             # Project CRUD
│   ├── pages.py                # Page rendering + navigation
│   ├── detection.py            # Layout detection trigger + results
│   ├── panels.py               # Panel edit persistence
│   └── export.py               # CBZ generation + download
│
├── core/
│   ├── pdf_renderer.py         # PyMuPDF: PDF → page JPEG
│   ├── layout_detector.py      # surya + OpenCV: image → bounding boxes
│   ├── panel_store.py          # Read/write panels.json
│   ├── cbz_exporter.py         # Crop panels → stream into ZIP
│   └── project_manager.py     # Project directory lifecycle
│
└── static/                     # Built React app (served by FastAPI)
```

### 2.2 Frontend Components

```
src/
├── App.jsx                     # Router, global state
│
├── pages/
│   ├── Home.jsx                # Project list + import
│   └── Editor.jsx              # Main editing view
│
├── components/
│   ├── PanelCanvas.jsx         # react-konva canvas with panel overlays
│   ├── PanelList.jsx           # Ordered panel list, drag to reorder
│   ├── PageStrip.jsx           # Thumbnail strip for page navigation
│   ├── Toolbar.jsx             # Tool mode selector + actions
│   ├── DetectionControls.jsx   # Sensitivity slider + re-detect button
│   └── ExportDialog.jsx        # Quality, page range, download
│
├── hooks/
│   ├── usePanels.js            # Panel state + undo/redo
│   ├── usePageRenderer.js      # Fetch + cache page images
│   └── useProject.js           # Project metadata + API calls
│
└── api/
    └── client.js               # Typed API wrappers around fetch()
```

---

## 3. Tech Stack

### Backend

| Component | Library | Rationale |
|---|---|---|
| Web framework | FastAPI | Async, fast, auto-docs, easy static file serving |
| PDF rendering | PyMuPDF (fitz) | Best performance for scanned PDFs, per-page rendering |
| Layout detection | surya | Pre-trained document layout model, no fine-tuning needed |
| Image fallback | OpenCV | Contour/morphology detection for simpler pages |
| Image processing | Pillow | Panel cropping, JPEG encoding |
| CBZ output | Python zipfile | CBZ is ZIP — no extra dependency needed |
| Concurrency | asyncio + ThreadPoolExecutor | Keep API responsive during CPU-heavy tasks |

### Frontend

| Component | Library | Rationale |
|---|---|---|
| Framework | React 18 + Vite | Fast build, modern hooks, small bundle |
| Canvas editor | react-konva | Touch-friendly canvas, draggable/resizable shapes |
| State management | Zustand | Lightweight, no boilerplate, easy undo/redo |
| Drag to reorder | dnd-kit | Accessible, touch-first drag-and-drop |
| HTTP client | fetch() + SWR | Native fetch with stale-while-revalidate caching |
| Styling | Tailwind CSS | Utility-first, responsive, no CSS files |
| PWA | vite-plugin-pwa | Service worker, manifest, installable on Android |

### Infrastructure

| Concern | Tool |
|---|---|
| Local run | `python app.py` |
| Remote access | Cloudflare Tunnel (`cloudflared`) |
| Optional isolation | Docker Compose |

---

## 4. Data Flow

### 4.1 PDF Import

```
User selects PDF file
        │
        ▼
POST /projects          (multipart upload, streams to disk)
        │
        ▼
Project directory created
source.pdf saved
Metadata written to project.json
        │
        ▼
Response: { project_id, page_count, title }
        │
        ▼
Frontend navigates to Editor view
```

### 4.2 Page View + Detection

```
User navigates to page N
        │
        ▼
GET /projects/{id}/pages/{n}/image
        │
        ├── Cache hit?  → return cached JPEG immediately
        │
        └── Cache miss? → PyMuPDF renders page at 150dpi
                          JPEG saved to pages/00N.jpg
                          JPEG returned as response
        │
        ▼
Frontend displays page image in canvas

GET /projects/{id}/pages/{n}/panels
        │
        ├── panels.json has data for page N? → return saved panels
        │
        └── No data? → run surya layout detection
                       convert regions to panel boxes
                       save to panels.json
                       return panel list
        │
        ▼
Frontend draws panel overlays on canvas
```

### 4.3 Panel Edit → Save

```
User edits a panel (drag/resize/delete/add)
        │
        ▼
Frontend updates local state immediately (no API call)
Undo stack updated
        │
        ▼
Debounce 500ms
        │
        ▼
PUT /projects/{id}/pages/{n}/panels   (full panel list for page)
        │
        ▼
Backend writes panels.json atomically
```

### 4.4 CBZ Export

```
User clicks Export
        │
        ▼
POST /projects/{id}/export   { quality, page_from, page_to }
        │
        ▼
Background task starts
For each page in range:
    render page image (or use cache)
    load panel list for page
    for each panel:
        crop region from page image
        encode as JPEG at requested quality
        write to ZIP stream
Write ComicInfo.xml
        │
        ▼
GET /projects/{id}/export/progress   (polling or WebSocket)
        │
        ▼
Export complete → output.cbz written
        │
        ▼
GET /projects/{id}/export/download   → file download response
```

---

## 5. Concurrency Model

The backend uses FastAPI's async handlers. CPU-heavy work (rendering, detection, export) runs in a `ThreadPoolExecutor` to avoid blocking the event loop. Each project has at most one active background task at a time.

```python
# Pattern used for blocking tasks
async def detect_layout(project_id, page_num):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, _blocking_detect, project_id, page_num)
    return result
```

---

## 6. PWA Offline Strategy

The PWA service worker uses a **network-first** strategy. Since all data is local, offline use isn't a primary goal — the service worker's main purpose is to make the app installable on Android and provide a fast app shell load.

- App shell (HTML, CSS, JS): cached on install
- API responses and page images: not cached (always fresh from local backend)
