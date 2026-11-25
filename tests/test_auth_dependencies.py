from uuid import uuid4
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import jwt
import pytest

from fastapi import HTTPException

from app.api.dependencies import get_current_user


@patch("app.api.dependencies.decode_access_token")
def test_get_current_user_success(mock_decode):

    db = MagicMock()

    user_id = uuid4()

    user = SimpleNamespace(
        id=user_id,
        email="harsh@example.com",
        is_active=True,
    )

    mock_decode.return_value = {
        "sub": str(user_id)
    }

    db.scalar.return_value = user

    result = get_current_user(
        token="valid_token",
        db=db,
    )

    assert result == user
    assert result.id == user_id
    assert result.is_active is True


@patch("app.api.dependencies.decode_access_token")
def test_get_current_user_invalid_token(mock_decode):

    db = MagicMock()

    mock_decode.side_effect = jwt.InvalidTokenError(
        "Invalid token"
    )

    with pytest.raises(HTTPException) as exc:

        get_current_user(
            token="invalid_token",
            db=db,
        )

    assert exc.value.status_code == 401
    db.scalar.assert_not_called()


@patch("app.api.dependencies.decode_access_token")
def test_get_current_user_expired_token(mock_decode):

    db = MagicMock()

    mock_decode.side_effect = jwt.ExpiredSignatureError(
        "Token expired"
    )

    with pytest.raises(HTTPException) as exc:

        get_current_user(
            token="expired_token",
            db=db,
        )

    assert exc.value.status_code == 401


@patch("app.api.dependencies.decode_access_token")
def test_get_current_user_malformed_uuid(mock_decode):

    db = MagicMock()

    mock_decode.return_value = {
        "sub": "this-is-not-a-valid-uuid"
    }

    with pytest.raises(HTTPException) as exc:

        get_current_user(
            token="valid_token",
            db=db,
        )

    assert exc.value.status_code == 401
    db.scalar.assert_not_called()


@patch("app.api.dependencies.decode_access_token")
def test_get_current_user_not_found(mock_decode):

    db = MagicMock()

    user_id = uuid4()

    mock_decode.return_value = {
        "sub": str(user_id)
    }

    db.scalar.return_value = None

    with pytest.raises(HTTPException) as exc:

        get_current_user(
            token="valid_token",
            db=db,
        )

    assert exc.value.status_code == 401


@patch("app.api.dependencies.decode_access_token")
def test_get_current_user_inactive(mock_decode):

    db = MagicMock()

    user_id = uuid4()

    user = SimpleNamespace(
        id=user_id,
        is_active=False,
    )

    mock_decode.return_value = {
        "sub": str(user_id)
    }

    db.scalar.return_value = user

    with pytest.raises(HTTPException) as exc:

        get_current_user(
            token="valid_token",
            db=db,
        )

    assert exc.value.status_code == 401