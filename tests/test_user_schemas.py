from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.user import User
from app.schemas.user import UserCreate, UserResponse


def test_user_create_valid_data():
    user = UserCreate(
        name="Harsh Tomar",
        email="harsh@example.com",
        password="securepassword123"
    )

    assert user.name == "Harsh Tomar"
    assert user.email == "harsh@example.com"


def test_user_create_invalid_email():
    with pytest.raises(ValidationError):
        UserCreate(
            name="Harsh Tomar",
            email="invalid-email",
            password="securepassword123"
        )


def test_user_create_short_password():
    with pytest.raises(ValidationError):
        UserCreate(
            name="Harsh Tomar",
            email="harsh@example.com",
            password="short"
        )


def test_user_create_short_name():
    with pytest.raises(ValidationError):
        UserCreate(
            name="H",
            email="harsh@example.com",
            password="securepassword123"
        )


def test_user_create_long_name():
    with pytest.raises(ValidationError):
        UserCreate(
            name="A" * 101,
            email="harsh@example.com",
            password="securepassword123"
        )


def test_user_response_from_sqlalchemy_object():
    user = User(
        id=uuid4(),
        name="Harsh Tomar",
        email="harsh@example.com",
        password_hash="some_argon2_hash",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )

    response = UserResponse.model_validate(user)

    assert response.name == "Harsh Tomar"
    assert response.email == "harsh@example.com"
    assert response.is_active is True


def test_user_response_does_not_expose_password_hash():
    user = User(
        id=uuid4(),
        name="Harsh Tomar",
        email="harsh@example.com",
        password_hash="some_argon2_hash",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )

    response = UserResponse.model_validate(user)

    assert "password_hash" not in response.model_dump()

import pytest
from pydantic import ValidationError

from app.schemas.auth import UserLogin, TokenResponse


def test_user_login_valid_data():
    login = UserLogin(
        email="harsh@example.com",
        password="mypassword123"
    )

    assert login.email == "harsh@example.com"
    assert login.password == "mypassword123"


def test_user_login_invalid_email():
    with pytest.raises(ValidationError):
        UserLogin(
            email="invalid-email",
            password="mypassword123"
        )


def test_user_login_empty_password():
    with pytest.raises(ValidationError):
        UserLogin(
            email="harsh@example.com",
            password=""
        )


def test_token_response():
    token = TokenResponse(
        access_token="sample.jwt.token"
    )

    assert token.access_token == "sample.jwt.token"
    assert token.token_type == "bearer"