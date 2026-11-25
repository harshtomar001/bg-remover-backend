from uuid import uuid4
from unittest.mock import MagicMock

import pytest

from app.services import image_service


def test_save_completed_image_success(monkeypatch):
    db = MagicMock()
    user_id = uuid4()

    monkeypatch.setattr(image_service, "save_image", MagicMock())
    monkeypatch.setattr(image_service, "delete_image", MagicMock())

    result = image_service.save_completed_image(
        db=db,
        user_id=user_id,
        original_filename="photo.jpg",
        original_data=b"original",
        processed_data=b"processed",
        content_type="image/jpeg",
        model_used="birefnet",
    )

    assert result.user_id == user_id
    assert result.status == "completed"
    assert result.size_bytes == len(b"original")
    assert result.original_storage_key.endswith(".jpg")
    assert result.processed_storage_key.endswith(".png")

    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(result)


def test_save_completed_image_database_failure_cleans_files(monkeypatch):
    db = MagicMock()
    db.commit.side_effect = RuntimeError("Database failure")

    saved_keys = []

    def mock_save(key, data):
        saved_keys.append(key)

    mock_delete = MagicMock()

    monkeypatch.setattr(image_service, "save_image", mock_save)
    monkeypatch.setattr(image_service, "delete_image", mock_delete)

    with pytest.raises(RuntimeError):
        image_service.save_completed_image(
            db=db,
            user_id=uuid4(),
            original_filename="photo.jpg",
            original_data=b"original",
            processed_data=b"processed",
            content_type="image/jpeg",
        )

    db.rollback.assert_called_once()
    assert len(saved_keys) == 2
    assert mock_delete.call_count == 2


def test_get_user_image_found():
    db = MagicMock()
    user_id = uuid4()
    image_id = uuid4()

    expected_image = MagicMock()
    db.scalar.return_value = expected_image

    result = image_service.get_user_image(db, user_id, image_id)

    assert result == expected_image
    db.scalar.assert_called_once()


def test_get_user_image_not_found():
    db = MagicMock()
    db.scalar.return_value = None

    result = image_service.get_user_image(
        db,
        uuid4(),
        uuid4(),
    )

    assert result is None


def test_delete_user_image_success(monkeypatch):
    db = MagicMock()
    user_id = uuid4()
    image_id = uuid4()

    image = MagicMock()
    image.original_storage_key = "users/test/originals/a.jpg"
    image.processed_storage_key = "users/test/processed/a.png"

    monkeypatch.setattr(
        image_service,
        "get_user_image",
        lambda db, user_id, image_id: image,
    )

    mock_delete = MagicMock()
    monkeypatch.setattr(image_service, "delete_image", mock_delete)

    result = image_service.delete_user_image(db, user_id, image_id)

    assert result is True
    db.delete.assert_called_once_with(image)
    db.commit.assert_called_once()
    assert mock_delete.call_count == 2


def test_delete_user_image_not_found(monkeypatch):
    db = MagicMock()

    monkeypatch.setattr(
        image_service,
        "get_user_image",
        lambda db, user_id, image_id: None,
    )

    result = image_service.delete_user_image(
        db,
        uuid4(),
        uuid4(),
    )

    assert result is False
    db.delete.assert_not_called()
    db.commit.assert_not_called()