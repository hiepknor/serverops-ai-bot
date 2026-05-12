from __future__ import annotations

from app.config import get_settings
from app.core.audit import AuditStore
from app.core.logging import configure_logging


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    AuditStore.from_database_url(settings.database_url).initialize()


if __name__ == "__main__":
    main()

