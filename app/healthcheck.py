from __future__ import annotations

from pathlib import Path

from app.config import get_settings
from app.core.audit import AuditStore
from app.core.confirmations import ConfirmationStore


def main() -> None:
    settings = get_settings()
    store = AuditStore.from_database_url(settings.database_url)
    store.initialize()
    ConfirmationStore.from_database_url(settings.database_url).initialize()
    if not Path(store.database_path).is_file():
        raise SystemExit("audit database is not available")


if __name__ == "__main__":
    main()
