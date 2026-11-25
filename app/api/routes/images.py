from math import ceil
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.image import ImageResponse, ImageHistoryResponse
from app.services.image_service import (
    get_user_image,
    get_user_image_history,
    delete_user_image,
    get_user_image_file,
)
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
)

router = APIRouter(prefix="/images", tags=["Images"])


@router.get("/history", response_model=ImageHistoryResponse)
def image_history(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    return get_user_image_history(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )


@router.get("/{image_id}", response_model=ImageResponse)
def image_details(
        image_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    image = get_user_image(db, current_user.id, image_id)

    if image is None:
        raise HTTPException(status_code=404, detail="Image not found.")

    return image


@router.delete("/{image_id}")
def delete_image_endpoint(
        image_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    deleted = delete_user_image(db, current_user.id, image_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Image not found.")

    return {"message": "Image deleted successfully."}


@router.get("/{image_id}/original")
def get_original_image(
        image_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):

    try:
        result = get_user_image_file(
            db=db,
            user_id=current_user.id,
            image_id=image_id,
            variant="original",
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Image not found.",
            )

        image_data, content_type = result

        return Response(
            content=image_data,
            media_type=content_type,
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Image file not found.",
        )


@router.get("/{image_id}/processed")
def get_processed_image(
        image_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):

    try:
        result = get_user_image_file(
            db=db,
            user_id=current_user.id,
            image_id=image_id,
            variant="processed",
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Image not found.",
            )

        image_data, content_type = result

        return Response(
            content=image_data,
            media_type=content_type,
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Image file not found.",
        )