from __future__ import annotations

import logging

from app.core.logging import configure_logging


def test_configure_logging_suppresses_http_client_info_logs() -> None:
    configure_logging("INFO")

    assert logging.getLogger("httpx").getEffectiveLevel() >= logging.WARNING
    assert logging.getLogger("httpcore").getEffectiveLevel() >= logging.WARNING
