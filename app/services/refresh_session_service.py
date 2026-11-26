import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.models.refresh_session import RefreshSession
from app.models.user import User


class InvalidRefreshSessionError(Exception):
    """The refresh credential is invalid, expired, revoked, or reused."""


class InactiveRefreshUserError(Exception):
    """The account associated with a refresh session is disabled."""


@dataclass(frozen=True)
class PersistentSessionTokens:
    access_token: str
    refresh_token: str


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def create_persistent_session(db: Session, user: User) -> PersistentSessionTokens:
    """Issue the same access/refresh pair for password and Google sign-in."""
    now = datetime.now(timezone.utc)
    raw_token = _new_refresh_token()
    session = RefreshSession(
        user_id=user.id,
        family_id=uuid.uuid4(),
        token_hash=_token_hash(raw_token),
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(session)
    db.commit()
    return PersistentSessionTokens(create_access_token(str(user.id)), raw_token)


def rotate_refresh_session(db: Session, raw_token: str) -> tuple[User, PersistentSessionTokens]:
    """Atomically rotate one refresh token; replay revokes its entire family."""
    token_hash = _token_hash(raw_token)
    session = db.scalar(
        select(RefreshSession).where(RefreshSession.token_hash == token_hash).with_for_update()
    )
    if session is None:
        raise InvalidRefreshSessionError

    now = datetime.now(timezone.utc)
    if session.revoked_at is not None:
        if session.replaced_by_id is not None:
            db.execute(
                update(RefreshSession)
                .where(RefreshSession.family_id == session.family_id, RefreshSession.revoked_at.is_(None))
                .values(revoked_at=now)
            )
            db.commit()
        raise InvalidRefreshSessionError

    if _utc(session.expires_at) <= now:
        session.revoked_at = now
        db.commit()
        raise InvalidRefreshSessionError

    user = db.get(User, session.user_id)
    if user is None or not user.is_active:
        session.revoked_at = now
        db.commit()
        raise InactiveRefreshUserError

    replacement_token = _new_refresh_token()
    replacement = RefreshSession(
        user_id=session.user_id,
        family_id=session.family_id,
        token_hash=_token_hash(replacement_token),
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(replacement)
    db.flush()
    session.revoked_at = now
    session.replaced_by_id = replacement.id
    db.commit()
    return user, PersistentSessionTokens(create_access_token(str(user.id)), replacement_token)


def revoke_refresh_session(db: Session, raw_token: str | None) -> None:
    if not raw_token:
        return
    session = db.scalar(select(RefreshSession).where(RefreshSession.token_hash == _token_hash(raw_token)))
    if session is not None and session.revoked_at is None:
        session.revoked_at = datetime.now(timezone.utc)
        db.commit()
