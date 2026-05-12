from __future__ import annotations

import pytest

from app.tools.log_tools import LogAccessError, read_log_tail, resolve_log_target


def test_read_log_tail_uses_only_allowlisted_target_and_redacts(tmp_path) -> None:
    log_file = tmp_path / "nginx-error.log"
    log_file.write_text(
        "line 1\nOPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz\nline 3\n",
        encoding="utf-8",
    )

    result = read_log_tail(
        "nginx_errors",
        [f"nginx_errors:{log_file}"],
        line_limit=2,
    )

    assert result.name == "nginx_errors"
    assert "line 1" not in result.content
    assert "line 3" in result.content
    assert "sk-abcdefghijklmnopqrstuvwxyz" not in result.content
    assert "[REDACTED]" in result.content


def test_resolve_log_target_rejects_unlisted_target(tmp_path) -> None:
    log_file = tmp_path / "app.log"
    log_file.write_text("ok\n", encoding="utf-8")

    with pytest.raises(LogAccessError):
        resolve_log_target("../app", [f"app:{log_file}"])
