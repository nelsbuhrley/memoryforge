"""Application configuration."""

from pathlib import Path
from pydantic import BaseModel


class Config(BaseModel):
    """MemoryForge configuration."""

    db_path: Path = Path.home() / ".memoryforge" / "memoryforge.db"
    uploads_dir: Path = Path.home() / ".memoryforge" / "uploads"
    api_host: str = "127.0.0.1"
    api_port: int = 9147
    max_upload_size_mb: int = 100
    parse_now_max_pages: int = 50
    default_easiness_factor: float = 2.5
    default_interleave_ratio: float = 0.3
    nightly_token_budget: int = 100000

    def ensure_dirs(self) -> None:
        """Create required directories if they don't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)


def get_config() -> Config:
    """Return the application config."""
    return Config()
