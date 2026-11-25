from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User

from app.schemas.user import (
    UserResponse,
    UserUpdate,
    UserDeleteResponse,
)

from app.api.dependencies import get_current_user

from app.services.user_service import (
    get_user_profile,
    update_user_profile,
    delete_user_account,
)


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get("/me", response_model=UserResponse)
def get_my_profile(
        current_user: User = Depends(get_current_user),
):
    return get_user_profile(current_user)


@router.patch("/me", response_model=UserResponse)
def update_my_profile(
        user_data: UserUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    return update_user_profile(
        db,
        current_user,
        user_data,
    )


@router.delete(
    "/me",
    response_model=UserDeleteResponse,
)
def delete_my_account(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    delete_user_account(db, current_user)

    return UserDeleteResponse(
        message="Account deleted successfully."
    )