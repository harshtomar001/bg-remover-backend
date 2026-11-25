import pytest
from pathlib import Path

from app.services import image_storage_service as storage


def test_get_storage_path_valid_key(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_ROOT", tmp_path)

    result = storage.get_storage_path("originals/user1/image1.png")

    assert result == tmp_path / "originals" / "user1" / "image1.png"


def test_get_storage_path_rejects_absolute_path(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_ROOT", tmp_path)

    with pytest.raises(ValueError):
        storage.get_storage_path(str(tmp_path / "secret.txt"))


def test_get_storage_path_rejects_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_ROOT", tmp_path)

    with pytest.raises(ValueError):
        storage.get_storage_path("../secret.txt")


def test_get_storage_path_rejects_empty_key(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_ROOT", tmp_path)

    with pytest.raises(ValueError):
        storage.get_storage_path("")


def test_get_storage_path_rejects_nested_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_ROOT", tmp_path)

    with pytest.raises(ValueError):
        storage.get_storage_path("originals/user1/../../secret.txt")

def test_save_image_success(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_ROOT", tmp_path)

    image_data = b"fake-image-content"

    result = storage.save_image(
        "originals/user1/image1.png",
        image_data
    )

    assert result.exists()
    assert result.is_file()
    assert result.read_bytes() == image_data


def test_save_image_creates_directories(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_ROOT", tmp_path)

    image_data = b"test-image"

    result = storage.save_image(
        "originals/user1/nested/image.png",
        image_data
    )

    assert result.exists()
    assert result.parent.exists()


def test_save_image_rejects_empty_data(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_ROOT", tmp_path)

    with pytest.raises(ValueError):
        storage.save_image(
            "originals/user1/image.png",
            b""
        )


def test_save_image_rejects_non_bytes(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_ROOT", tmp_path)

    with pytest.raises(ValueError):
        storage.save_image(
            "originals/user1/image.png",
            "not bytes"
        )


def test_save_image_preserves_existing_file_on_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_ROOT", tmp_path)

    storage.save_image(
        "originals/user1/image.png",
        b"original-content"
    )

    destination = tmp_path / "originals" / "user1" / "image.png"

    original_replace = storage.os.replace

    def failing_replace(source, target):
        raise OSError("Simulated filesystem failure")

    monkeypatch.setattr(storage.os, "replace", failing_replace)

    with pytest.raises(OSError):
        storage.save_image(
            "originals/user1/image.png",
            b"new-content"
        )

    assert destination.read_bytes() == b"original-content"

    monkeypatch.setattr(storage.os, "replace", original_replace)

def test_delete_image_success(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_ROOT", tmp_path)

    storage.save_image("originals/user1/image.png", b"image-content")

    result = storage.delete_image("originals/user1/image.png")

    assert result is True
    assert not (tmp_path / "originals/user1/image.png").exists()


def test_delete_image_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_ROOT", tmp_path)

    result = storage.delete_image("originals/user1/missing.png")

    assert result is False


def test_delete_image_rejects_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_ROOT", tmp_path)

    with pytest.raises(ValueError):
        storage.delete_image("../outside.png")


def test_delete_image_rejects_absolute_path(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_ROOT", tmp_path)

    with pytest.raises(ValueError):
        storage.delete_image(str(tmp_path / "outside.png"))


def test_delete_image_file_is_actually_removed(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_ROOT", tmp_path)

    storage.save_image("processed/user1/result.png", b"processed-content")
    file_path = tmp_path / "processed/user1/result.png"

    assert file_path.exists()

    storage.delete_image("processed/user1/result.png")

    assert not file_path.exists()


from uuid import uuid4

def test_delete_user_images_success(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_ROOT", tmp_path)

    user_id = uuid4()

    storage.save_image(
        f"users/{user_id}/originals/image.png",
        b"original"
    )
    storage.save_image(
        f"users/{user_id}/processed/image.png",
        b"processed"
    )

    result = storage.delete_user_images(user_id)

    assert result is True
    assert not (tmp_path / "users" / str(user_id)).exists()

def test_delete_user_images_missing_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_ROOT", tmp_path)

    result = storage.delete_user_images(uuid4())

    assert result is False
def test_delete_user_images_preserves_other_users(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_ROOT", tmp_path)

    user1 = uuid4()
    user2 = uuid4()

    storage.save_image(f"users/{user1}/originals/a.png", b"user1")
    storage.save_image(f"users/{user2}/originals/b.png", b"user2")

    storage.delete_user_images(user1)

    assert not (tmp_path / "users" / str(user1)).exists()
    assert (tmp_path / "users" / str(user2) / "originals" / "b.png").exists()

def test_delete_user_images_rejects_invalid_user_id(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_ROOT", tmp_path)

    with pytest.raises(ValueError):
        storage.delete_user_images("../another_user")


def test_delete_user_images_removes_nested_directories(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_ROOT", tmp_path)

    user_id = uuid4()

    storage.save_image(
        f"users/{user_id}/originals/nested/folder/image.png",
        b"image"
    )

    storage.delete_user_images(user_id)

    assert not (tmp_path / "users" / str(user_id)).exists()

def test_read_image_success(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_ROOT", tmp_path)

    image_data = b"test-image-content"
    storage.save_image("users/test/originals/image.png", image_data)

    result = storage.read_image("users/test/originals/image.png")

    assert result == image_data


def test_read_image_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_ROOT", tmp_path)

    with pytest.raises(FileNotFoundError):
        storage.read_image("users/test/originals/missing.png")


def test_read_image_rejects_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_ROOT", tmp_path)

    with pytest.raises(ValueError):
        storage.read_image("../outside.png")