import hashlib
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException, Request, Response
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes import auth as auth_routes
from app.core.security import hash_password
from app.db.database import Base
from app.schemas.auth import GoogleLogin, UserLogin
from app.models.refresh_session import RefreshSession
from app.models.user import User
from app.services.refresh_session_service import (
    InvalidRefreshSessionError,
    InactiveRefreshUserError,
    create_persistent_session,
    revoke_refresh_session,
    rotate_refresh_session,
)

ORIGIN = "http://localhost:5173"


@pytest.fixture
def db_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    yield factory
    Base.metadata.drop_all(engine)
    engine.dispose()


def make_request(origin: str, cookie: str | None = None) -> Request:
    headers = [(b"origin", origin.encode("ascii"))]
    if cookie:
        headers.append((b"cookie", f"bgremove_refresh={cookie}".encode("ascii")))
    return Request({"type": "http", "method": "POST", "path": "/auth/refresh", "headers": headers})


def make_user(db: Session, *, active: bool = True, google: bool = False) -> User:
    user = User(
        name="Test User",
        email=f"user-{id(db)}-{google}@example.com",
        password_hash=None if google else hash_password("StrongPassword123"),
        google_sub=f"google-{id(db)}" if google else None,
        is_active=active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_refresh_rotates_token_and_keeps_raw_value_out_of_database(db_factory):
    with db_factory() as db:
        user = make_user(db)
        first = create_persistent_session(db, user)
        old_row = db.scalar(select(RefreshSession).where(RefreshSession.user_id == user.id))

        assert first.refresh_token not in old_row.token_hash
        refreshed_user, second = rotate_refresh_session(db, first.refresh_token)
        db.refresh(old_row)

        assert refreshed_user.id == user.id
        assert second.access_token
        assert second.refresh_token != first.refresh_token
        assert old_row.revoked_at is not None
        assert old_row.replaced_by_id is not None
        assert db.scalar(select(RefreshSession).where(RefreshSession.token_hash == second.refresh_token)) is None


def test_expired_refresh_token_is_revoked(db_factory):
    with db_factory() as db:
        user = make_user(db)
        tokens = create_persistent_session(db, user)
        row = db.scalar(select(RefreshSession).where(RefreshSession.user_id == user.id))
        row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.commit()

        with pytest.raises(InvalidRefreshSessionError):
            rotate_refresh_session(db, tokens.refresh_token)
        db.refresh(row)
        assert row.revoked_at is not None


def test_invalid_refresh_token_is_rejected(db_factory):
    with db_factory() as db, pytest.raises(InvalidRefreshSessionError):
        rotate_refresh_session(db, "not-a-valid-refresh-token")


def test_revoked_refresh_token_is_rejected_and_replay_revokes_family(db_factory):
    with db_factory() as db:
        user = make_user(db)
        first = create_persistent_session(db, user)
        _, second = rotate_refresh_session(db, first.refresh_token)

        with pytest.raises(InvalidRefreshSessionError):
            rotate_refresh_session(db, first.refresh_token)

        current_hash = hashlib.sha256(second.refresh_token.encode()).hexdigest()
        current = db.scalar(select(RefreshSession).where(RefreshSession.token_hash == current_hash))
        assert current.revoked_at is not None


def test_logout_revokes_only_the_selected_session(db_factory):
    with db_factory() as db:
        user = make_user(db)
        first = create_persistent_session(db, user)
        second = create_persistent_session(db, user)
        revoke_refresh_session(db, first.refresh_token)

        with pytest.raises(InvalidRefreshSessionError):
            rotate_refresh_session(db, first.refresh_token)
        refreshed_user, _ = rotate_refresh_session(db, second.refresh_token)
        assert refreshed_user.id == user.id


def test_inactive_user_cannot_refresh(db_factory):
    with db_factory() as db:
        user = make_user(db)
        tokens = create_persistent_session(db, user)
        user.is_active = False
        db.commit()
        with pytest.raises(InactiveRefreshUserError):
            rotate_refresh_session(db, tokens.refresh_token)


def test_password_login_creates_refresh_cookie(db_factory, monkeypatch):
    monkeypatch.setattr("app.services.auth_service.verify_password", lambda _password, _hashed: True)
    with db_factory() as db:
        user = User(
            name="Test User",
            email="password@example.com",
            password_hash="test-hash",
            is_active=True,
        )
        db.add(user)
        db.commit()
        email = user.email
        response = Response()
        result = auth_routes.login(make_request(ORIGIN), UserLogin(email=email, password="StrongPassword123"), response, db)
        assert result.access_token
        cookie = response.headers["set-cookie"].lower()
        assert "httponly" in cookie and "samesite=lax" in cookie and "path=/auth" in cookie
        assert "bgremove_refresh" not in result.model_dump_json()


def test_google_login_creates_refresh_cookie(db_factory, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.auth.verify_google_token",
        lambda _credential: {"google_sub": "google-subject", "email": "google@example.com", "name": "Google User"},
    )
    with db_factory() as db:
        response = Response()
        result = auth_routes.google_login(make_request(ORIGIN), GoogleLogin(credential="google-id-token"), response, db)
        assert result.access_token
        assert "httponly" in response.headers["set-cookie"].lower()


def test_refresh_and_logout_require_an_allowed_origin(db_factory):
    with db_factory() as db:
        with pytest.raises(HTTPException) as refresh_error:
            auth_routes.refresh(make_request("https://evil.example"), Response(), db)
        with pytest.raises(HTTPException) as logout_error:
            auth_routes.logout(make_request("https://evil.example"), Response(), db)
        assert refresh_error.value.status_code == 403
        assert logout_error.value.status_code == 403


def test_refresh_endpoint_rotates_cookie_and_logout_clears_it(db_factory):
    with db_factory() as db:
        user = make_user(db)
        tokens = create_persistent_session(db, user)
        logout_tokens = create_persistent_session(db, user)
        refresh_response = Response()
        refreshed = auth_routes.refresh(make_request(ORIGIN, tokens.refresh_token), refresh_response, db)
        assert refreshed.access_token
        rotated_cookie = refresh_response.headers["set-cookie"]
        assert "httponly" in rotated_cookie.lower()

        logout_response = Response()
        result = auth_routes.logout(make_request(ORIGIN, logout_tokens.refresh_token), logout_response, db)
        assert result["message"]
        assert "max-age=0" in logout_response.headers["set-cookie"].lower()


def test_multiple_devices_have_independent_token_families(db_factory):
    with db_factory() as db:
        user = make_user(db)
        first = create_persistent_session(db, user)
        second = create_persistent_session(db, user)
        rows = db.scalars(select(RefreshSession).where(RefreshSession.user_id == user.id)).all()
        assert len(rows) == 2
        assert rows[0].family_id != rows[1].family_id
        _, rotated = rotate_refresh_session(db, first.refresh_token)
        _, still_valid = rotate_refresh_session(db, second.refresh_token)
        assert rotated.refresh_token != still_valid.refresh_token
