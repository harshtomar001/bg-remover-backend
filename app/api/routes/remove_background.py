from io import BytesIO
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool
from app.services.model_registry import model_manager
from app.services.birefnet_service import birefnet_service


router = APIRouter()

MAX_FILE_SIZE = 15 * 1024 * 1024

ALLOWED_FORMATS = {
    "JPEG",
    "PNG",
    "WEBP",
}


@router.post("/remove-background")
async def remove_background(file: UploadFile = File(...)):
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

    return Response(
        content=output_bytes,
        media_type="image/png",
        headers={
            "Content-Disposition": 'attachment; filename="background_removed.png"'
        },
    )