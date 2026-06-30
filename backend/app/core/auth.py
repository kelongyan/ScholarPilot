"""Minimal request authentication and RBAC helpers."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Annotated, Any, Literal, cast

from fastapi import Depends, Header, HTTPException, status

from app.core.config import get_settings

UserRole = Literal["user", "kb_manager", "admin"]

_ROLE_RANK: dict[UserRole, int] = {
    "user": 1,
    "kb_manager": 2,
    "admin": 3,
}


@dataclass(frozen=True)
class CurrentUser:
    """Authenticated actor and coarse-grained RBAC scope."""

    actor_id: str
    role: UserRole
    knowledge_base_ids: frozenset[str] | None = None
    auth_enabled: bool = True

    def can_access_knowledge_base(self, knowledge_base_id: str | None) -> bool:
        if self.role == "admin":
            return True
        if not knowledge_base_id:
            return True
        if self.knowledge_base_ids is None:
            return True
        return knowledge_base_id in self.knowledge_base_ids

    def has_role_at_least(self, role: UserRole) -> bool:
        return _ROLE_RANK[self.role] >= _ROLE_RANK[role]


def get_current_user(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> CurrentUser:
    """Resolve the current user from Authorization when auth is enabled."""
    settings = get_settings()
    if not settings.auth_enabled:
        return CurrentUser(
            actor_id=settings.auth_dev_actor_id,
            role="admin",
            knowledge_base_ids=None,
            auth_enabled=False,
        )

    token = _read_bearer_token(authorization)
    user = _user_from_static_token(token) or _user_from_jwt(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_min_role(role: UserRole) -> Callable[[CurrentUser], CurrentUser]:
    """FastAPI dependency factory for coarse role checks."""

    def dependency(
        current_user: Annotated[CurrentUser, Depends(get_current_user)],
    ) -> CurrentUser:
        if not current_user.has_role_at_least(role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role for this operation.",
            )
        return current_user

    return dependency


def require_knowledge_base_access(
    current_user: CurrentUser,
    knowledge_base_id: str | None,
) -> None:
    """Raise 403 when the actor cannot access a knowledge base."""
    if not current_user.can_access_knowledge_base(knowledge_base_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Knowledge base access denied.",
        )


def filter_by_knowledge_base_access[T](
    items: Iterable[T],
    current_user: CurrentUser,
    *,
    get_knowledge_base_id: Callable[[T], str | None],
) -> list[T]:
    """Filter ORM objects or DTOs to the actor's allowed knowledge bases."""
    return [
        item
        for item in items
        if current_user.can_access_knowledge_base(get_knowledge_base_id(item))
    ]


def _read_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token.strip()


def _user_from_static_token(token: str) -> CurrentUser | None:
    settings = get_settings()
    configured_tokens = [
        (settings.auth_admin_token, "admin", "admin"),
        (settings.auth_kb_manager_token, "kb_manager", "kb-manager"),
        (settings.auth_user_token, "user", "user"),
    ]
    for configured_token, role, actor_id in configured_tokens:
        if configured_token and hmac.compare_digest(token, configured_token):
            return CurrentUser(actor_id=actor_id, role=cast(UserRole, role))
    return None


def _user_from_jwt(token: str) -> CurrentUser | None:
    settings = get_settings()
    if not settings.auth_jwt_secret:
        return None

    parts = token.split(".")
    if len(parts) != 3:
        return None

    signing_input = f"{parts[0]}.{parts[1]}".encode()
    expected = hmac.new(
        settings.auth_jwt_secret.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    try:
        supplied = _base64url_decode(parts[2])
    except (ValueError, binascii.Error):
        return None
    if not hmac.compare_digest(expected, supplied):
        return None

    try:
        header = json.loads(_base64url_decode(parts[0]))
        claims = json.loads(_base64url_decode(parts[1]))
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError, binascii.Error):
        return None

    if header.get("alg") != "HS256":
        return None
    exp = claims.get("exp")
    if isinstance(exp, int | float) and exp < time.time():
        return None

    role = claims.get("role")
    if role not in _ROLE_RANK:
        return None

    actor_id = _first_string(
        claims.get("sub"),
        claims.get("actor_id"),
        claims.get("user_id"),
    )
    knowledge_base_ids = _read_knowledge_base_ids(claims)
    return CurrentUser(
        actor_id=actor_id or "jwt-user",
        role=cast(UserRole, role),
        knowledge_base_ids=knowledge_base_ids,
    )


def _read_knowledge_base_ids(claims: dict[str, Any]) -> frozenset[str] | None:
    raw = claims.get("knowledge_base_ids", claims.get("kb_ids"))
    if raw is None:
        return None
    if not isinstance(raw, list):
        return frozenset()
    return frozenset(str(item) for item in raw if str(item))


def _first_string(*values: object) -> str:
    for value in values:
        if isinstance(value, str) and value:
            return value
    return ""


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode("ascii"))
