import uuid
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.image import Image
from app.services.image_storage_service import (
    save_image,
    delete_image,
    read_image,
)

from sqlalchemy import select


def save_completed_image(
        db: Session,
        user_id: UUID,
        original_filename: str,
        original_data: bytes,
        processed_data: bytes,
        content_type: str,
        model_used: str | None = None,
) -> Image:

    image_id = uuid.uuid4()

    extension = Path(original_filename).suffix.lower()

    if extension not in {".png", ".jpg", ".jpeg", ".webp"}:
        extension = ".png"

    base_key = f"users/{user_id}"

    original_key = f"{base_key}/originals/{image_id}{extension}"
    processed_key = f"{base_key}/processed/{image_id}.png"

    saved_keys = []

    try:
        # Save original image
        save_image(original_key, original_data)
        saved_keys.append(original_key)

        # Save processed image
        save_image(processed_key, processed_data)
        saved_keys.append(processed_key)

        # Create database record
        image = Image(
            id=image_id,
            user_id=user_id,
            original_filename=original_filename,
            original_storage_key=original_key,
            processed_storage_key=processed_key,
            content_type=content_type,
            size_bytes=len(original_data),
            status="completed",
            model_used=model_used,
        )

        db.add(image)
        db.commit()
        db.refresh(image)

        return image

    except Exception:
        db.rollback()

        # Remove files if database operation fails
        for storage_key in saved_keys:
            try:
                delete_image(storage_key)
            except OSError:
                pass

        raise


def get_user_image(
        db: Session,
        user_id: UUID,
        image_id: UUID,
) -> Image | None:

    return db.scalar(
        select(Image).where(
            Image.id == image_id,
            Image.user_id == user_id,
            )
    )

def delete_user_image(
        db: Session,
        user_id: UUID,
        image_id: UUID,
) -> bool:

    image = get_user_image(db, user_id, image_id)

    if image is None:
        return False

    storage_keys = [
        image.original_storage_key,
        image.processed_storage_key,
    ]

    # Remove the database record.
    try:
        db.delete(image)
        db.commit()
    except Exception:
        db.rollback()
        raise

    # Clean up physical files after successful database deletion.
    for storage_key in storage_keys:
        if storage_key:
            delete_image(storage_key)

    return True

from sqlalchemy import select, func


def get_user_image_history(
        db: Session,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
):
    if page < 1:
        raise ValueError("Page must be at least 1.")

    if not 1 <= page_size <= 100:
        raise ValueError("Page size must be between 1 and 100.")

    total = db.scalar(
        select(func.count())
        .select_from(Image)
        .where(Image.user_id == user_id)
    ) or 0

    images = db.scalars(
        select(Image)
        .where(Image.user_id == user_id)
        .order_by(Image.created_at.desc(), Image.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    total_pages = (total + page_size - 1) // page_size

    return {
        "items": images,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def get_user_image_file(
        db: Session,
        user_id: UUID,
        image_id: UUID,
        variant: str,
) -> tuple[bytes, str] | None:

    # Validate requested image variant
    if variant not in ("original", "processed"):
        raise ValueError("Invalid image variant.")

    # Fetch image belonging to the authenticated user
    image = get_user_image(db, user_id, image_id)

    if image is None:
        return None

    # Select the appropriate storage key
    if variant == "original":
        storage_key = image.original_storage_key
        content_type = image.content_type

    else:
        storage_key = image.processed_storage_key
        content_type = "image/png"

        if storage_key is None:
            raise FileNotFoundError("Processed image does not exist.")

    # Read image bytes from storage
    image_data = read_image(storage_key)

    return image_data, content_type