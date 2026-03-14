# UI Design & Mockups

## 1. Design Principles

- **Touch-first:** All interactive targets minimum 44×44px. Primary interactions designed for thumbs on a 10" tablet
- **Canvas is king:** The page image and panel overlays occupy maximum screen space
- **Progressive disclosure:** Advanced options (detection tuning, templates) are hidden until needed
- **Instant feedback:** Panel edits update immediately in the canvas; saves happen silently in the background
- **Mobile-first layout:** Single-column layout that scales up for desktop — not a desktop UI crammed onto mobile

---

## 2. Screens

### 2.1 Home Screen — Project List

The landing screen. Lists all projects with resume capability.

```
┌─────────────────────────────────────────┐
│  PDF2CBZ                        [+ New] │  ← Header bar
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ 📖 The Art of War               │    │  ← Project card
│  │    312 pages · 205MB            │    │
│  │    Last edited: page 42         │    │
│  │    ████████░░  64% detected     │    │  ← Detection progress bar
│  │                    [Resume] [⋮] │    │  ← Resume button + overflow menu
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ 📖 Dune                         │    │
│  │    412 pages · 287MB            │    │
│  │    Exported Mar 12              │    │
│  │    ████████████  100% detected  │    │
│  │             [Download CBZ] [⋮]  │    │
│  └─────────────────────────────────┘    │
│                                         │
│         [+ Import PDF]                  │  ← Primary CTA
│                                         │
└─────────────────────────────────────────┘
```

**Overflow menu [⋮] options:** Rename, Delete project, Clear page cache

**Import flow:** Tapping [+ Import PDF] opens the native file picker. Upload progress shown inline replacing the button.

---

### 2.2 Editor Screen — Layout (Tablet Landscape)

The main editing view. Designed for a 10" tablet in landscape.

```
┌──────────────────────────────────────────────────────────────────────┐
│  ← Art of War    Page 42 / 312    [Detect] [Template▾] [Export]     │  ← Top bar
├────────────┬─────────────────────────────────────────┬───────────────┤
│            │                                         │               │
│  PANELS    │                                         │  1 ┌────────┐ │
│            │     ╔══════════════╗                    │    │ Col 1  │ │
│  1 Col 1   │     ║              ║                    │  2 │        │ │
│  2 Col 2   │     ║   [Panel 1]  ║                    │    └────────┘ │
│  3 Figure  │     ║              ║   ╔════════════╗   │               │
│            │     ╚══════════════╝   ║            ║   │  2 ┌────────┐ │
│  ─────     │                        ║  [Panel 2] ║   │    │ Col 2  │ │
│            │     ╔══════════════╗   ║            ║   │    │        │ │
│  ☑ Header  │     ║   [Panel 3]  ║   ╚════════════╝   │    └────────┘ │
│    (excl.) │     ║   (Figure)   ║                    │               │
│            │     ╚══════════════╝   ┄┄┄┄┄┄┄┄┄┄┄┄    │  3 ┌────────┐ │
│            │                        [Header - off]   │    │ Figure │ │
│  [+ Add]   │                                         │    └────────┘ │
│            │                                         │               │
├────────────┴────────────┬────────────────────────────┴───────────────┤
│  [Select] [Draw] [Split]│  [Undo] [Redo]   Zoom: [─────●──────]      │  ← Toolbar
├─────────────────────────┴──────────────────────────────────────────  ┤
│ [◄◄] [◄] [●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●] [►] [►►]       │  ← Page strip
└──────────────────────────────────────────────────────────────────────┘

Left panel (200px):      Panel list — drag handles to reorder
Centre:                  Canvas — page image + panel overlay boxes
Right panel (170px):     Panel thumbnails — visual reading order preview
Bottom toolbar:          Tool mode + undo/redo + zoom
Bottom strip:            Page thumbnail navigator
```

---

### 2.3 Editor Screen — Layout (Phone / Tablet Portrait)

On portrait or phone, the panel list collapses to a bottom drawer.

```
┌────────────────────────────────────┐
│ ← Art of War    p.42/312  [≡] [⋮] │  ← Top bar (compact)
├────────────────────────────────────┤
│                                    │
│                                    │
│      ╔══════════════╗              │
│      ║              ║              │
│      ║   [Panel 1]  ║   ╔══════╗  │
│      ║              ║   ║  P2  ║  │
│      ╚══════════════╝   ╚══════╝  │
│                                    │
│      ╔══════════════╗              │
│      ║   [Panel 3]  ║              │
│      ╚══════════════╝              │
│                                    │
├────────────────────────────────────┤
│ [Select] [Draw] [Split] [↩] [↪]   │  ← Tool bar
├────────────────────────────────────┤
│ [◄] ●●●●●●●●●●●●●●●●●●●●●● [►]   │  ← Page strip (compact)
└────────────────────────────────────┘
                 ↕ drag
┌────────────────────────────────────┐  ← Bottom drawer (panels list)
│  Panels (3 shown, 1 hidden)        │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  1  Col 1             ☑  [✕]      │
│  2  Col 2             ☑  [✕]      │
│  3  Figure            ☑  [✕]      │
│  ✗  Header (excluded) ☐  [✕]      │
│                   [+ Add Panel]    │
└────────────────────────────────────┘
```

---

### 2.4 Panel Selection State

When a panel is selected, handles appear and a context action bar shows below the canvas.

```
      ╔══╦══════════════╦══╗
      ║  ║              ║  ║   ← Corner resize handles (large for touch)
      ╠══╣              ╠══╣
      ║  ║  [Panel 1]   ║  ║   ← Edge resize handles
      ║  ║  SELECTED    ║  ║
      ╠══╣              ╠══╣
      ║  ║              ║  ║
      ╚══╩══════════════╩══╝
              ↑
      ┌───────────────────────────────┐
      │  [Split H] [Split V] [Delete] │  ← Context action bar (appears below canvas)
      └───────────────────────────────┘
```

Handle sizes: corner handles 28×28px, edge handles 16×44px (tall for touch accuracy on horizontal edges).

---

### 2.5 Draw New Panel Mode

When Draw tool is active, dragging on the canvas creates a new panel.

```
   Canvas in Draw mode:
   Cursor changes to crosshair

   User drags to define region:

   ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
   │  (dashed blue rect) │
   │  Width: 680px       │
   │  Height: 420px      │
   └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘

   On release: panel is created, mode reverts to Select
```

---

### 2.6 Split Panel Interaction

Selecting a panel then tapping [Split H] or [Split V] shows a drag-to-position divider.

```
   After [Split H]:

   ╔══════════════╗
   ║              ║
   ║  Panel 1A    ║
   ║              ║
   ╠══════════════╣  ← Draggable divider line (blue, 4px, 44px touch area)
   ║              ║
   ║  Panel 1B    ║
   ║              ║
   ╚══════════════╝

         [Confirm Split]  [Cancel]
```

---

### 2.7 Detection Controls Panel

Accessed via the [Detect] button in the top bar. Slides down as a panel.

```
┌──────────────────────────────────────────┐
│  Layout Detection                    [×] │
├──────────────────────────────────────────┤
│  Model:    ● surya    ○ opencv           │
│                                          │
│  Sensitivity:  Low ──────●────── High   │
│                       0.45               │
│                                          │
│  Exclude:  ☑ Headers    ☑ Footers        │
│            ☑ Page numbers                │
│                                          │
│       [Re-detect This Page]              │
│       [Re-detect All Pages]              │
└──────────────────────────────────────────┘
```

"Re-detect All Pages" shows a confirmation: "This will overwrite manually edited pages too. Continue?"

---

### 2.8 Template Controls

Accessed via [Template▾] dropdown in top bar.

```
┌──────────────────────────────┐
│  Templates                   │
├──────────────────────────────┤
│  [Save current as template…] │
├──────────────────────────────┤
│  Apply template:             │
│  ○ Standard 2-col (3 panels) │
│  ○ Title page (1 panel)      │
├──────────────────────────────┤
│  Apply to pages:             │
│  From [  5 ] to [ 40 ]       │
│  ☐ Overwrite edited pages    │
│         [Apply Template]     │
└──────────────────────────────┘
```

---

### 2.9 Export Dialog

```
┌──────────────────────────────────────────┐
│  Export CBZ                          [×] │
├──────────────────────────────────────────┤
│  Title:  [ The Art of War            ]   │
│                                          │
│  Page range:  [  1 ] to [ 312 ]          │
│               ○ All pages                │
│               ● Custom range             │
│                                          │
│  JPEG quality:                           │
│  Small ────────────●─── Large            │
│              85%  (~48 MB est.)          │
│                                          │
│  ⚠ 12 pages have no panels detected     │
│    [Detect missing pages first]          │
│                                          │
│           [Export CBZ]                   │
└──────────────────────────────────────────┘
```

During export, the button becomes a progress indicator:

```
│  ████████████░░░░░░  62%                 │
│  Page 192 of 312 · 523 panels so far     │
│                [Cancel]                  │
```

On completion:

```
│  ✅  Export complete!                    │
│      The Art of War.cbz  ·  47.2 MB      │
│                                          │
│           [Download CBZ]                 │
└──────────────────────────────────────────┘
```

---

## 3. Colour System

| Token | Value | Use |
|---|---|---|
| `--primary` | `#2563EB` | Buttons, selected panel border, active handles |
| `--primary-light` | `#DBEAFE` | Panel overlay fill (low opacity) |
| `--excluded` | `#94A3B8` | Excluded panel overlay (dashed border) |
| `--figure` | `#7C3AED` | Figure-type panel border |
| `--destructive` | `#DC2626` | Delete button, error state |
| `--surface` | `#F8FAFC` | Sidebar/panel backgrounds |
| `--border` | `#E2E8F0` | Dividers, inactive borders |
| `--text-primary` | `#0F172A` | Main text |
| `--text-secondary` | `#64748B` | Labels, metadata |

**Panel overlay colours:**

| Panel type | Border | Fill |
|---|---|---|
| text (included) | `#2563EB` solid 2px | `rgba(37,99,235,0.08)` |
| figure (included) | `#7C3AED` solid 2px | `rgba(124,58,237,0.08)` |
| excluded | `#94A3B8` dashed 2px | `rgba(148,163,184,0.05)` |
| selected | `#2563EB` solid 3px | `rgba(37,99,235,0.12)` |
| new (drawing) | `#2563EB` dashed 2px | `rgba(37,99,235,0.05)` |

---

## 4. Typography

| Element | Font | Size | Weight |
|---|---|---|---|
| App title | System UI | 18px | 600 |
| Page heading | System UI | 16px | 600 |
| Body / labels | System UI | 14px | 400 |
| Panel number badge | Monospace | 13px | 600 |
| Metadata / secondary | System UI | 12px | 400 |

---

## 5. Responsive Breakpoints

| Breakpoint | Layout |
|---|---|
| < 600px (phone) | Single column, bottom drawer for panel list |
| 600–1024px (tablet portrait) | Single column with collapsible bottom drawer |
| ≥ 1024px (tablet landscape / desktop) | Three-column: panel list + canvas + thumbnail strip |

---

## 6. Keyboard Shortcuts (Desktop)

| Key | Action |
|---|---|
| `V` | Select tool |
| `D` | Draw tool |
| `S` | Split tool |
| `Delete` / `Backspace` | Delete selected panel |
| `Ctrl+Z` | Undo |
| `Ctrl+Shift+Z` | Redo |
| `←` / `→` | Previous / next page |
| `E` | Open export dialog |
| `Escape` | Deselect / cancel draw |
| `+` / `-` | Zoom in / out |
