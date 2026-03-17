# PDF2CBZ — Project Documentation

Convert scanned PDF books into navigable CBZ comic book files with automatic panel detection and a touch-friendly editor.

---

## Document Index

| Document | Description |
|---|---|
| [Requirements](./01-requirements.md) | Functional and non-functional requirements |
| [Architecture](./02-architecture.md) | System design, tech stack, and component overview |
| [Data Model](./03-data-model.md) | Data structures, file formats, and storage layout |
| [API Reference](./04-api-reference.md) | FastAPI backend endpoint specifications |
| [UI Design & Mockups](./05-ui-design.md) | Screen layouts, interaction patterns, and mockups |
| [Pipeline Design](./06-pipeline.md) | PDF rendering, layout detection, and CBZ export pipeline |
| [Development Guide](./07-dev-guide.md) | Setup, running locally, project structure |
| [Deployment](./08-deployment.md) | Cloudflare Tunnel setup and optional VPS deployment |

---

## Project Summary

**Problem:** Scanned book PDFs have small text and multi-column layouts that are difficult to read on mobile devices. Zooming and panning is a poor user experience.

**Solution:** Convert each page into individually cropped panel images, packaged as a CBZ file. CBZ readers navigate panel-by-panel, allowing each text block to fill the screen.

**Approach:**
- Python backend renders PDF pages and auto-detects text columns/paragraphs using computer vision
- React web frontend (PWA) lets the user review and edit detected panels on a touch screen
- Output is a standard CBZ file readable by Moon+, Panels, Komga, and any comic reader

---

## Quick Start

```bash
git clone https://github.com/yourname/pdf2cbz
cd pdf2cbz
pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..
python app.py
# Open http://localhost:8000 in your browser
```

For remote access from a tablet, see [Deployment](./08-deployment.md).

## How to Test the Current Implementation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start the backend API + static UI (single process):

```bash
python app.py
```

3. Open `http://localhost:8000` in your browser.
   - The HTML app now defaults API calls to the same origin, so the upload form works immediately when served by FastAPI.
   - If you host the HTML separately (for example via `python -m http.server`), set the **API base** field in the header to `http://localhost:8000` and click **Save**.

4. End-to-end smoke flow:
   - Import a scanned PDF
   - Click **Resume** on that project
   - Open a page, trigger **Detect**
   - Trigger **Export** and then poll `/api/tasks/{task_id}`

