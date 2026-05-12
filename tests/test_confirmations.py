from __future__ import annotations

from app.core.confirmations import ConfirmationStore, confirmation_text_for


def test_confirmation_store_creates_and_matches_pending_text(tmp_path) -> None:
    store = ConfirmationStore(tmp_path / "serverops.db")
    text = confirmation_text_for("restart_service", "nginx")

    pending = store.create(
        user_id=100,
        role="owner",
        action="restart_service",
        target="nginx",
        confirmation_text=text,
    )

    matched = store.get_pending_by_text(user_id=100, confirmation_text=text)

    assert pending.id == 1
    assert matched is not None
    assert matched.action == "restart_service"
    assert matched.target == "nginx"


def test_confirmation_store_marks_confirmation_used(tmp_path) -> None:
    store = ConfirmationStore(tmp_path / "serverops.db")
    text = confirmation_text_for("restart_container", "api")
    pending = store.create(
        user_id=100,
        role="admin",
        action="restart_container",
        target="api",
        confirmation_text=text,
    )

    store.mark_confirmed(pending.id)

    assert store.get_pending_by_text(user_id=100, confirmation_text=text) is None


def test_confirmation_text_can_be_reused_by_different_users(tmp_path) -> None:
    store = ConfirmationStore(tmp_path / "serverops.db")
    text = confirmation_text_for("restart_service", "nginx")

    first = store.create(
        user_id=100,
        role="admin",
        action="restart_service",
        target="nginx",
        confirmation_text=text,
    )
    second = store.create(
        user_id=200,
        role="admin",
        action="restart_service",
        target="nginx",
        confirmation_text=text,
    )

    assert first.id != second.id
    assert store.get_pending_by_text(user_id=100, confirmation_text=text) is not None
    assert store.get_pending_by_text(user_id=200, confirmation_text=text) is not None


def test_confirmation_text_is_exact_and_human_readable() -> None:
    assert confirmation_text_for("restart_service", "nginx") == "CONFIRM RESTART SERVICE NGINX"
