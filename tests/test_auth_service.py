from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.schemas.user import UserCreate
from app.schemas.auth import UserLogin

from app.services.auth_service import (
    register_user,
    login_user,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
)


# -------------------------
# Registration Tests
# -------------------------

@patch("app.services.auth_service.hash_password")
def test_register_user_success(mock_hash_password):
    db = MagicMock()

    mock_hash_password.return_value = "hashed_password"

    db.scalar.return_value = None

    user_data = UserCreate(
        name="Harsh Tomar",
        email="harsh@example.com",
        password="StrongPassword123",
    )

    user = register_user(db, user_data)

    assert isinstance(user, User)
    assert user.email == "harsh@example.com"
    assert user.password_hash == "hashed_password"

    mock_hash_password.assert_called_once_with(
        "StrongPassword123"
    )

    db.add.assert_called_once_with(user)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(user)


def test_register_user_duplicate_email():
    db = MagicMock()

    existing_user = SimpleNamespace(
        email="harsh@example.com"
    )

    db.scalar.return_value = existing_user

    user_data = UserCreate(
        name="Harsh Tomar",
        email="harsh@example.com",
        password="StrongPassword123",
    )

    with pytest.raises(EmailAlreadyRegisteredError):
        register_user(db, user_data)

    db.add.assert_not_called()
    db.commit.assert_not_called()


@patch("app.services.auth_service.hash_password")
def test_register_user_handles_concurrent_duplicate(
        mock_hash_password,
):
    db = MagicMock()

    mock_hash_password.return_value = "hashed_password"

    db.scalar.side_effect = [
        None,
        SimpleNamespace(email="harsh@example.com"),
    ]

    db.commit.side_effect = IntegrityError(
        "INSERT INTO users",
        {},
        Exception("Unique constraint violation"),
    )

    user_data = UserCreate(
        name="Harsh Tomar",
        email="harsh@example.com",
        password="StrongPassword123",
    )

    with pytest.raises(EmailAlreadyRegisteredError):
        register_user(db, user_data)

    db.rollback.assert_called_once()


# -------------------------
# Login Tests
# -------------------------

@patch("app.services.auth_service.create_access_token")
@patch("app.services.auth_service.verify_password")
def test_login_user_success(
        mock_verify_password,
        mock_create_token,
):
    db = MagicMock()

    user = SimpleNamespace(
        id="1234",
        email="harsh@example.com",
        password_hash="hashed_password",
        is_active=True,
    )

    db.scalar.return_value = user

    mock_verify_password.return_value = True
    mock_create_token.return_value = "mock_jwt_token"

    credentials = UserLogin(
        email="harsh@example.com",
        password="StrongPassword123",
    )

    token = login_user(db, credentials)

    assert token == "mock_jwt_token"

    mock_verify_password.assert_called_once_with(
        "StrongPassword123",
        "hashed_password",
    )

    mock_create_token.assert_called_once_with("1234")


@patch("app.services.auth_service.verify_password")
def test_login_user_wrong_password(mock_verify_password):
    db = MagicMock()

    user = SimpleNamespace(
        id="1234",
        email="harsh@example.com",
        password_hash="hashed_password",
        is_active=True,
    )

    db.scalar.return_value = user
    mock_verify_password.return_value = False

    credentials = UserLogin(
        email="harsh@example.com",
        password="WrongPassword123",
    )

    with pytest.raises(InvalidCredentialsError):
        login_user(db, credentials)


def test_login_user_nonexistent_email():
    db = MagicMock()
    db.scalar.return_value = None

    credentials = UserLogin(
        email="unknown@example.com",
        password="StrongPassword123",
    )

    with pytest.raises(InvalidCredentialsError):
        login_user(db, credentials)


@patch("app.services.auth_service.verify_password")
def test_login_user_inactive_account(mock_verify_password):
    db = MagicMock()

    user = SimpleNamespace(
        id="1234",
        email="harsh@example.com",
        password_hash="hashed_password",
        is_active=False,
    )

    db.scalar.return_value = user
    mock_verify_password.return_value = True

    credentials = UserLogin(
        email="harsh@example.com",
        password="StrongPassword123",
    )

    with pytest.raises(InvalidCredentialsError):
        login_user(db, credentials)