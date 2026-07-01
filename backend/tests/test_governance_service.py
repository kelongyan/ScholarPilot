"""Tests for governance service membership access rules."""

from __future__ import annotations

from types import SimpleNamespace

from app.core.auth import CurrentUser
from app.services import governance_service


def test_claim_scoped_user_can_access_allowed_kb_without_configured_members(
    monkeypatch,
) -> None:
    user = CurrentUser(
        actor_id="user-1",
        role="kb_manager",
        knowledge_base_ids=frozenset({"kb-allowed"}),
    )

    monkeypatch.setattr(
        governance_service.governance_repo,
        "get_member",
        lambda db, **kwargs: None,
    )
    monkeypatch.setattr(
        governance_service.governance_repo,
        "has_memberships",
        lambda db, **kwargs: False,
    )

    assert governance_service.can_access_knowledge_base(object(), user, "kb-allowed")
    assert not governance_service.can_access_knowledge_base(object(), user, "kb-denied")


def test_membership_role_allows_required_level(monkeypatch) -> None:
    user = CurrentUser(actor_id="manager-1", role="kb_manager")
    member = SimpleNamespace(role="manager", status="active")

    monkeypatch.setattr(
        governance_service.governance_repo,
        "get_member",
        lambda db, **kwargs: member,
    )
    monkeypatch.setattr(
        governance_service.governance_repo,
        "has_memberships",
        lambda db, **kwargs: True,
    )

    assert governance_service.can_access_knowledge_base(
        object(),
        user,
        "kb-1",
        min_member_role="contributor",
    )
    assert not governance_service.can_access_knowledge_base(
        object(),
        user,
        "kb-1",
        min_member_role="owner",
    )


def test_configured_membership_takes_precedence_over_claim_scope(monkeypatch) -> None:
    user = CurrentUser(
        actor_id="manager-1",
        role="kb_manager",
        knowledge_base_ids=frozenset({"kb-1"}),
    )
    member = SimpleNamespace(role="manager", status="active")

    monkeypatch.setattr(
        governance_service.governance_repo,
        "get_member",
        lambda db, **kwargs: member,
    )

    assert not governance_service.can_access_knowledge_base(
        object(),
        user,
        "kb-1",
        min_member_role="owner",
    )


def test_membership_configured_kb_denies_non_member(monkeypatch) -> None:
    user = CurrentUser(actor_id="manager-1", role="kb_manager")

    monkeypatch.setattr(
        governance_service.governance_repo,
        "get_member",
        lambda db, **kwargs: None,
    )
    monkeypatch.setattr(
        governance_service.governance_repo,
        "has_memberships",
        lambda db, **kwargs: True,
    )

    assert not governance_service.can_access_knowledge_base(object(), user, "kb-1")
