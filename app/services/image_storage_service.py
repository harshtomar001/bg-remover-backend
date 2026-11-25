from pathlib import Path
import os
import tempfile
import shutil
from uuid import UUID

from app.core.config import settings


STORAGE_ROOT = Path(settings.STORAGE_ROOT).resolve()


def get_storage_path(storage_key: str) -> Path:
    if not storage_key or not isinstance(storage_key, str):
        raise ValueError("Storage key must be a non-empty string.")

    relative_path = Path(storage_key)

    if relative_path.is_absolute():
        raise ValueError("Absolute storage paths are not allowed.")

    # Reject any parent-directory traversal component.
    if ".." in relative_path.parts:
        raise ValueError("Path traversal is not allowed.")

    resolved_path = (STORAGE_ROOT / relative_path).resolve()

    try:
        resolved_path.relative_to(STORAGE_ROOT)
    except ValueError:
        raise ValueError("Invalid storage key: path traversal detected.")

    return resolved_path

def save_image(storage_key: str, image_data: bytes) -> Path:
    """
    Save image bytes atomically inside permanent storage.
    """

    if not isinstance(image_data, bytes) or not image_data:
        raise ValueError("Image data must be non-empty bytes.")

    destination = get_storage_path(storage_key)

    destination.parent.mkdir(parents=True, exist_ok=True)

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=destination.parent,
                prefix=".upload_",
                suffix=".tmp",
                delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(image_data)
            temp_file.flush()
            os.fsync(temp_file.fileno())

        os.replace(temp_path, destination)

        return destination

    except Exception:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        raise



def read_image(storage_key: str) -> bytes:
    file_path = get_storage_path(storage_key)

    if not file_path.is_file():
        raise FileNotFoundError(f"Image not found: {storage_key}")

    return file_path.read_bytes()

def delete_image(storage_key: str) -> bool:
    file_path = get_storage_path(storage_key)

    if not file_path.is_file():
        return False

    file_path.unlink()
    return True

def delete_user_images(user_id: UUID) -> bool:
    if not isinstance(user_id, UUID):
        raise ValueError("user_id must be a valid UUID.")

    user_storage_key = f"users/{user_id}"
    user_directory = get_storage_path(user_storage_key)

    if not user_directory.exists():
        return False

    if not user_directory.is_dir():
        raise ValueError("User storage path is not a directory.")

    shutil.rmtree(user_directory)

    return True