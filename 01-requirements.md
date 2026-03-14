# Requirements

## 1. Overview

PDF2CBZ is a personal tool that converts scanned PDF books into CBZ comic book archive files. The primary motivation is improving readability of scanned books on Android phones and tablets by breaking each page into readable panels rather than requiring the user to zoom and pan.

---

## 2. User Stories

### Core Workflow

| ID | As a user I want to... | So that... |
|---|---|---|
| US-01 | Upload a scanned PDF book | I can begin processing it |
| US-02 | See each page rendered at readable size | I can review the content |
| US-03 | See automatically detected panels overlaid on each page | I don't have to manually draw every panel |
| US-04 | Edit detected panels (move, resize, delete, add, split) | I can correct detection errors |
| US-05 | Set the reading order of panels on a page | The CBZ navigates in the right sequence |
| US-06 | Apply panel edits from one page as a template to similar pages | I don't repeat work for uniform page layouts |
| US-07 | Export the result as a CBZ file | I can open it in my comic reader app |
| US-08 | Resume editing a project after closing the app | I don't lose work between sessions |
| US-09 | Access the app from my Android tablet over home WiFi | I can edit on the device I read on |

### Panel Detection

| ID | As a user I want to... | So that... |
|---|---|---|
| US-10 | Trigger re-detection on a page with different sensitivity | I can tune detection for tricky pages |
| US-11 | See multi-column pages split into separate left/right column panels | Columns read correctly in sequence |
| US-12 | Have figures and images detected as their own panels | Illustrations are preserved as panels |
| US-13 | Exclude headers, footers, and page numbers from panels | Noise isn't included in the output |

### Export

| ID | As a user I want to... | So that... |
|---|---|---|
| US-14 | Choose image quality (file size vs clarity) for export | I can balance storage space and readability |
| US-15 | Export a page range rather than the whole book | I can split a book into parts |
| US-16 | See export progress | I know the app is working on large files |

---

## 3. Functional Requirements

### 3.1 PDF Handling

- **FR-01** The system shall accept PDF files up to 300MB in size
- **FR-02** The system shall render PDF pages to images on demand (lazy rendering), not all at once
- **FR-03** Rendered page images shall be cached to disk to avoid re-rendering on revisit
- **FR-04** The system shall support PDFs consisting entirely of raster page scans (not text-based PDFs)
- **FR-05** The system shall display total page count and allow navigation to any page by number

### 3.2 Layout Detection

- **FR-06** The system shall automatically detect text block regions on each page using computer vision
- **FR-07** Detection shall handle single-column, double-column, and triple-column page layouts
- **FR-08** Detection shall identify figures and images as distinct regions from text blocks
- **FR-09** Detection results shall be returned as a list of bounding boxes with type labels (text, figure, header, footer)
- **FR-10** The user shall be able to adjust detection sensitivity and re-run detection on any page
- **FR-11** Header and footer regions shall be flagged and excluded from panel output by default
- **FR-12** Detection shall complete within 30 seconds per page on a modern consumer PC

### 3.3 Panel Editing

- **FR-13** The user shall be able to select any panel bounding box on the canvas
- **FR-14** The user shall be able to move a selected panel by dragging
- **FR-15** The user shall be able to resize a selected panel by dragging corner and edge handles
- **FR-16** The user shall be able to delete a selected panel
- **FR-17** The user shall be able to draw a new panel by dragging on empty canvas space
- **FR-18** The user shall be able to split a panel into two halves (horizontally or vertically)
- **FR-19** The user shall be able to reorder panels via a numbered list alongside the canvas
- **FR-20** Panel numbers shall be visible on the canvas as overlaid labels
- **FR-21** The user shall be able to undo and redo panel editing actions (minimum 20 steps)
- **FR-22** The user shall be able to apply the current page's panel layout as a template to a range of other pages

### 3.4 Project Management

- **FR-23** Each imported PDF shall create a named project stored in a local working directory
- **FR-24** Panel edits shall be auto-saved to disk after each change
- **FR-25** The user shall be able to open any previously created project
- **FR-26** The user shall be able to delete a project and its associated files

### 3.5 CBZ Export

- **FR-27** The system shall export panels as JPEG images cropped from the original page render
- **FR-28** Panel images shall be named to enforce reading order across pages
- **FR-29** The CBZ shall include a `ComicInfo.xml` metadata file
- **FR-30** The user shall be able to select JPEG quality (default 85%)
- **FR-31** The user shall be able to export a specific page range
- **FR-32** Export shall stream panels into the ZIP without loading all images into memory simultaneously
- **FR-33** The user shall be able to download the completed CBZ file from the UI

---

## 4. Non-Functional Requirements

### 4.1 Performance

- **NFR-01** Page rendering shall complete within 5 seconds per page at 150dpi on a 4-core CPU
- **NFR-02** The UI shall remain responsive (not block) while rendering or detection runs in the background
- **NFR-03** Panel edits (move, resize, delete) shall reflect in the UI within 100ms
- **NFR-04** CBZ export shall process at a minimum rate of 10 panels per second

### 4.2 Usability

- **NFR-05** The editing UI shall be fully operable by touch on a 10" Android tablet
- **NFR-06** Touch targets (handles, buttons) shall be a minimum of 44×44px
- **NFR-07** The app shall be installable as a PWA on Android (add to home screen)
- **NFR-08** The UI shall work in both portrait and landscape tablet orientations

### 4.3 Reliability

- **NFR-09** Panel edits shall be persisted within 1 second of the change occurring
- **NFR-10** The app shall recover gracefully from a backend restart without data loss
- **NFR-11** The system shall handle corrupt or partially scanned PDF pages without crashing

### 4.4 Storage

- **NFR-12** Cached page images shall be stored in a designated temp directory
- **NFR-13** The user shall be able to clear the page image cache from the UI
- **NFR-14** The system shall warn if available disk space drops below 500MB during export

### 4.5 Security & Privacy

- **NFR-15** The backend shall only bind to localhost by default (not exposed to the network without explicit configuration)
- **NFR-16** When using Cloudflare Tunnel, all traffic shall be encrypted via HTTPS
- **NFR-17** No PDF content shall be sent to any third-party service

---

## 5. Constraints

- The application runs on a single user's PC — no multi-user, no authentication required
- Processing (PDF rendering, layout detection) must run entirely on the local machine
- Output format is CBZ (ZIP of JPEG images) — no other output formats required in v1
- The backend is Python 3.10+; the frontend is a React PWA served by the backend
- No internet connection is required for core functionality (Cloudflare Tunnel is optional)

---

## 6. Out of Scope (v1)

- Text-based (non-scanned) PDFs with selectable text
- OCR / text extraction
- EPUB or PDF output formats
- Multi-user or cloud-hosted deployment
- Automatic deskewing or image enhancement (may be added in v2)
- Batch processing of multiple PDFs simultaneously
