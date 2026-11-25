from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import UserLogin, TokenResponse

from app.services.auth_service import (
    register_user,
    login_user,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
        user_data: UserCreate,
        db: Session = Depends(get_db),
):
    try:
        user = register_user(db, user_data)
        return user

    except EmailAlreadyRegisteredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
        credentials: UserLogin,
        db: Session = Depends(get_db),
):
    try:
        access_token = login_user(db, credentials)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
        )

    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )