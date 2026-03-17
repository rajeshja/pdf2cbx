from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config import settings
from routers import export, pages, panels, projects, system

app = FastAPI(title="PDF2CBZ", version="0.1.0")

app.include_router(projects.router)
app.include_router(pages.router)
app.include_router(panels.router)
app.include_router(export.router)
app.include_router(system.router)

static_dir = Path("static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def index():
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"name": "PDF2CBZ", "docs": "/docs"}


if __name__ == "__main__":
    uvicorn.run("app:app", host=settings.host, port=settings.port, reload=False)
