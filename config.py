from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PDF2CBZ_", env_file=".env")

    projects_dir: Path = Field(default=Path.home() / "pdf2cbz" / "projects")
    render_dpi: int = 150
    default_jpeg_quality: int = 85
    max_upload_size_mb: int = 300
    host: str = "127.0.0.1"
    port: int = 8000
    detection_model: str = "opencv"
    detection_confidence_threshold: float = 0.5
    max_undo_steps: int = 20


settings = Settings()
settings.projects_dir.mkdir(parents=True, exist_ok=True)
