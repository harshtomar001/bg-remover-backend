from io import BytesIO

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
    Depends,
)
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.services.model_registry import model_manager
from app.services.image_service import save_completed_image

from app.api.dependencies import get_optional_current_user
from app.db.database import get_db
from app.models.user import User


router = APIRouter()

MAX_FILE_SIZE = 15 * 1024 * 1024

ALLOWED_FORMATS = {
    "JPEG",
    "PNG",
    "WEBP",
}

FORMAT_CONTENT_TYPES = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}


@router.post("/remove-background")
async def remove_background(
        file: UploadFile = File(...),
        current_user: User | None = Depends(get_optional_current_user),
        db: Session = Depends(get_db),
):

    # --------------------------------------------------
    # 1. Validate uploaded file
    # --------------------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename was provided.",
        )

    image_bytes = await file.read(MAX_FILE_SIZE + 1)

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    if len(image_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Image size must not exceed 15 MB.",
        )

    try:
        with Image.open(BytesIO(image_bytes)) as image:

            image_format = image.format

            if image_format not in ALLOWED_FORMATS:
                raise HTTPException(
                    status_code=415,
                    detail="Only JPEG, PNG, and WebP images are supported.",
                )

            image.verify()

        with Image.open(BytesIO(image_bytes)) as image:
            original_image = image.copy()

    except UnidentifiedImageError:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not a valid image.",
        )

    except OSError:
        raise HTTPException(
            status_code=400,
            detail="The image file is corrupted or cannot be decoded.",
        )

    # --------------------------------------------------
    # 2. Run background-removal inference
    # --------------------------------------------------

    try:

        model = model_manager.get_model("birefnet")

        result = await run_in_threadpool(
            model.remove_background,
            original_image,
        )

        output_buffer = BytesIO()

        result.save(output_buffer, format="PNG")

        output_bytes = output_buffer.getvalue()

    except Exception as exc:

        print(f"Background removal failed: {exc}")

        raise HTTPException(
            status_code=500,
            detail="Background removal failed. Please try again.",
        ) from exc

    # --------------------------------------------------
    # 3. Persist images for authenticated users
    # --------------------------------------------------

    image_id = None

    if current_user is not None:

        try:

            saved_image = await run_in_threadpool(
                save_completed_image,
                db,
                current_user.id,
                file.filename,
                image_bytes,
                output_bytes,
                FORMAT_CONTENT_TYPES[image_format],
                "birefnet",
            )

            image_id = saved_image.id

        except Exception as exc:

            print(f"Image persistence failed: {exc}")

            raise HTTPException(
                status_code=500,
                detail="Image processing succeeded, but saving the image failed.",
            ) from exc

    # --------------------------------------------------
    # 4. Return processed PNG
    # --------------------------------------------------

    headers = {
        "Content-Disposition": 'attachment; filename="background_removed.png"'
    }

    # Guests do not receive an image ID.
    # Authenticated users receive their saved database ID.

    if image_id is not None:
        headers["X-Image-ID"] = str(image_id)

    return Response(
        content=output_bytes,
        media_type="image/png",
        headers=headers,
    )