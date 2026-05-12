from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse


def database_path_from_url(database_url: str) -> Path:
    parsed = urlparse(database_url)
    if parsed.scheme != "sqlite":
        raise ValueError("Only sqlite DATABASE_URL values are supported in the MVP")
    if parsed.netloc:
        raise ValueError("SQLite DATABASE_URL must use a local path")
    if not parsed.path:
        raise ValueError("SQLite DATABASE_URL must include a database path")
    return Path(parsed.path.lstrip("/"))

