"""Tests for audit log service behavior."""

from __future__ import annotations

from datetime import UTC, datetime

from app.services import audit_log_service


def test_log_event_persists_audit_record(monkeypatch) -> None:
    from app.repositories import audit_log_repo

    captured = {}

    def fake_create_audit_log(db, audit_log):
        audit_log.created_at = datetime(2026, 6, 30, tzinfo=UTC)
        captured["audit_log"] = audit_log
        return audit_log

    monkeypatch.setattr(audit_log_repo, "create_audit_log", fake_create_audit_log)

    log = audit_log_service.log_event(
        object(),
        action="document.uploaded",
        resource_type="document",
        resource_id="doc-1",
        knowledge_base_id="kb-1",
        detail_json={"title": "Handbook"},
    )

    assert log.audit_id
    assert log.actor_id == "system"
    assert log.action == "document.uploaded"
    assert log.resource_type == "document"
    assert log.resource_id == "doc-1"
    assert log.knowledge_base_id == "kb-1"
    assert log.detail_json == {"title": "Handbook"}
    assert captured["audit_log"] is log


def test_try_log_event_swallows_audit_failures() -> None:
    class BrokenDB:
        def __init__(self) -> None:
            self.rolled_back = False

        def add(self, obj) -> None:
            raise RuntimeError("database unavailable")

        def rollback(self) -> None:
            self.rolled_back = True

    db = BrokenDB()

    log = audit_log_service.try_log_event(
        db,
        action="agent_run.viewed",
        resource_type="agent_run",
        resource_id="run-1",
    )

    assert log is None
    assert db.rolled_back is True


def test_list_audit_logs_passes_filters(monkeypatch) -> None:
    from app.repositories import audit_log_repo

    captured = {}

    def fake_list_audit_logs(db, **kwargs):
        captured.update(kwargs)
        return []

    monkeypatch.setattr(audit_log_repo, "list_audit_logs", fake_list_audit_logs)
    created_from = datetime(2026, 6, 1, tzinfo=UTC)
    created_to = datetime(2026, 6, 30, tzinfo=UTC)

    logs = audit_log_service.list_audit_logs(
        object(),
        knowledge_base_id="kb-1",
        action="feedback.submitted",
        resource_type="answer_feedback",
        resource_id="fb-1",
        actor_id="system",
        created_from=created_from,
        created_to=created_to,
    )

    assert logs == []
    assert captured == {
        "knowledge_base_id": "kb-1",
        "action": "feedback.submitted",
        "resource_type": "answer_feedback",
        "resource_id": "fb-1",
        "actor_id": "system",
        "created_from": created_from,
        "created_to": created_to,
    }
