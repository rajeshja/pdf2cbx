# Development Guide

## 1. Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10+ | 3.11 recommended |
| Node.js | 18+ | For frontend build |
| pip | Latest | `pip install --upgrade pip` |
| Git | Any | |
| Disk space | ~5 GB | For Python deps including surya model weights |
| RAM | 8 GB min | 16 GB recommended for surya |

---

## 2. Project Structure

```
pdf2cbz/
├── app.py                      # FastAPI entry point
├── requirements.txt
├── config.py                   # Pydantic settings model
│
├── routers/                    # FastAPI route handlers
│   ├── __init__.py
│   ├── projects.py
│   ├── pages.py
│   ├── panels.py
│   ├── detection.py
│   └── export.py
│
├── core/                       # Business logic (no FastAPI dependencies)
│   ├── __init__.py
│   ├── pdf_renderer.py
│   ├── layout_detector.py
│   ├── panel_store.py
│   ├── cbz_exporter.py
│   └── project_manager.py
│
├── models/                     # Pydantic request/response models
│   ├── project.py
│   ├── panel.py
│   └── task.py
│
├── tests/
│   ├── test_renderer.py
│   ├── test_detector.py
│   ├── test_exporter.py
│   └── fixtures/               # Small test PDFs
│
├── frontend/                   # React + Vite source
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api/
│       │   └── client.js
│       ├── components/
│       │   ├── PanelCanvas.jsx
│       │   ├── PanelList.jsx
│       │   ├── PageStrip.jsx
│       │   ├── Toolbar.jsx
│       │   ├── DetectionControls.jsx
│       │   └── ExportDialog.jsx
│       ├── hooks/
│       │   ├── usePanels.js
│       │   ├── usePageRenderer.js
│       │   └── useProject.js
│       ├── pages/
│       │   ├── Home.jsx
│       │   └── Editor.jsx
│       └── store/
│           └── index.js        # Zustand stores
│
└── scripts/
    ├── download_models.py      # One-time model weight download
    └── dev.sh                  # Start backend + frontend dev servers
```

---

## 3. Setup

### 3.1 Clone and create virtual environment

```bash
git clone https://github.com/yourname/pdf2cbz
cd pdf2cbz

python -m venv venv
source venv/bin/activate          # Linux/Mac
# or
venv\Scripts\activate             # Windows
```

### 3.2 Install Python dependencies

```bash
pip install -r requirements.txt
```

**`requirements.txt`:**

```
fastapi==0.111.*
uvicorn[standard]==0.30.*
python-multipart==0.0.*       # multipart file upload
PyMuPDF==1.24.*
surya-ocr==0.5.*              # includes layout model
opencv-python-headless==4.10.*
Pillow==10.*
pydantic==2.*
pydantic-settings==2.*
aiofiles==23.*
python-jose==3.*              # for future auth if needed
pytest==8.*
httpx==0.27.*                 # for testing FastAPI
```

### 3.3 Download surya model weights

On first run, surya downloads ~500 MB of model weights. Run this once to pre-download:

```bash
python scripts/download_models.py
```

Weights are cached in `~/.cache/huggingface/`.

### 3.4 Install frontend dependencies

```bash
cd frontend
npm install
```

### 3.5 Build frontend (for production use)

```bash
cd frontend
npm run build
# Outputs to frontend/dist/ which FastAPI serves as static files
```

---

## 4. Running the Application

### 4.1 Production mode (built frontend)

```bash
# From project root (with venv activated)
python app.py
# Opens http://localhost:8000
```

### 4.2 Development mode (hot reload)

Run two terminals:

**Terminal 1 — Backend with auto-reload:**
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend dev server with proxy:**
```bash
cd frontend
npm run dev
# Vite dev server on http://localhost:5173
# API calls proxy to http://localhost:8000
```

Or use the convenience script:
```bash
./scripts/dev.sh
```

**`vite.config.js` proxy configuration:**
```javascript
export default {
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/projects': 'http://localhost:8000',  // static project images
    }
  }
}
```

### 4.3 Access from Android tablet

1. Find your PC's local IP: `ip addr` (Linux) or `ipconfig` (Windows)
2. Open `http://<your-pc-ip>:8000` in Chrome on your tablet
3. Tap the browser menu → "Add to Home Screen" to install as PWA

> The backend binds to `0.0.0.0` by default so it's reachable on your local network. If you want localhost-only, set `HOST=127.0.0.1` in your environment.

---

## 5. Configuration

Settings are loaded from environment variables or a `.env` file in the project root.

**`.env` (create this file, do not commit it):**

```env
PDF2CBZ_PROJECTS_DIR=/home/yourname/pdf2cbz/projects
PDF2CBZ_RENDER_DPI=150
PDF2CBZ_DEFAULT_JPEG_QUALITY=85
PDF2CBZ_MAX_UPLOAD_SIZE_MB=300
PDF2CBZ_HOST=0.0.0.0
PDF2CBZ_PORT=8000
PDF2CBZ_DETECTION_MODEL=surya
PDF2CBZ_OPEN_BROWSER=true
```

**`config.py`:**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    projects_dir: str = "~/pdf2cbz/projects"
    render_dpi: int = 150
    default_jpeg_quality: int = 85
    max_upload_size_mb: int = 300
    host: str = "0.0.0.0"
    port: int = 8000
    detection_model: str = "surya"
    open_browser: bool = True

    class Config:
        env_prefix = "PDF2CBZ_"
        env_file = ".env"
```

---

## 6. Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov=routers

# Run specific test file
pytest tests/test_renderer.py -v

# Run tests excluding slow integration tests
pytest -m "not slow"
```

**Test fixtures:** Small (5-page) scanned PDFs are in `tests/fixtures/`. These are committed to the repo. Do not commit full-size books.

---

## 7. Key Implementation Notes

### Panel coordinates

Panel `x`, `y`, `width`, `height` are always in **pixels relative to the rendered page image at the project's configured DPI**. They are NOT normalised or percentage-based (except in templates — see Data Model). This means:

- If DPI changes, cached panel coordinates become invalid for the new render size
- The frontend always receives the page's `source_width` and `source_height` and uses these to scale the canvas correctly

### Undo/redo

Undo history lives entirely in the frontend Zustand store. The backend only stores the current state. Each `PUT /panels` call overwrites the server state completely. The frontend sends the full panel array, not a diff.

### Detection is idempotent

`POST /detect` always overwrites panels for the requested page, even if panels were manually edited. The UI warns the user before re-detecting an edited page.

### CBZ filename sorting

CBZ readers rely on alphabetical sort order of filenames to determine reading order. Always use zero-padded numbers: `pdf2cbz_page_0042_panel_003.jpg` not `pdf2cbz_page_42_panel_3.jpg`.

---

## 8. Adding a New Detection Backend

To add a new layout detection model:

1. Create `core/detectors/my_detector.py` implementing:
   ```python
   def detect(image_path: str, confidence_threshold: float) -> list[dict]:
       """Returns list of panel dicts with x, y, width, height, type, confidence"""
       ...
   ```

2. Register in `core/layout_detector.py`:
   ```python
   DETECTORS = {
       "surya": surya_detector.detect,
       "opencv": opencv_detector.detect,
       "my_detector": my_detector.detect,   # add here
   }
   ```

3. Add the model name as a valid option in `models/panel.py`:
   ```python
   DetectionModel = Literal["surya", "opencv", "my_detector"]
   ```
