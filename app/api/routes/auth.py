from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import UserLogin, GoogleLogin, TokenResponse

from app.services.auth_service import (
    register_user,
    authenticate_password_user,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
)

from app.services.google_auth_service import (
    verify_google_token,
    GoogleTokenVerificationError,
    GoogleAuthConfigurationError,
)

from app.services.google_account_service import (
    authenticate_google_user,
    GoogleAccountConflictError,
    GoogleAccountDisabledError,
)

from app.core.config import settings
from app.services.refresh_session_service import (
    create_persistent_session,
    rotate_refresh_session,
    revoke_refresh_session,
    InvalidRefreshSessionError,
    InactiveRefreshUserError,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


def _require_allowed_origin(request: Request) -> None:
    origin = request.headers.get("origin", "").rstrip("/")
    if not origin or origin not in settings.FRONTEND_ORIGIN_LIST:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Request origin is not allowed.")


def _set_refresh_cookie(response: Response, token: str) -> None:
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        expires=expires_at,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        path=settings.REFRESH_COOKIE_PATH,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        path=settings.REFRESH_COOKIE_PATH,
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
        request: Request,
        credentials: UserLogin,
        response: Response,
        db: Session = Depends(get_db),
):
    _require_allowed_origin(request)
    try:
        user = authenticate_password_user(db, credentials)
        tokens = create_persistent_session(db, user)
        _set_refresh_cookie(response, tokens.refresh_token)
        return TokenResponse(
            access_token=tokens.access_token,
            token_type="bearer",
        )

    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post(
    "/google",
    response_model=TokenResponse,
)
def google_login(
        request: Request,
        credentials: GoogleLogin,
        response: Response,
        db: Session = Depends(get_db),
):
    _require_allowed_origin(request)
    # Step 1: Verify Google's ID token.
    try:
        google_user = verify_google_token(
            credentials.credential
        )

    except GoogleTokenVerificationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Google credential.",
        )

    except GoogleAuthConfigurationError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google authentication is not configured.",
        )

    # Step 2: Find or create the BGRemove user.
    try:
        user = authenticate_google_user(
            db=db,
            google_sub=google_user["google_sub"],
            email=google_user["email"],
            name=google_user["name"],
        )

    except GoogleAccountConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    except GoogleAccountDisabledError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is disabled.",
        )

    # Both password and Google authentication use the same persistent session service.
    tokens = create_persistent_session(db, user)
    _set_refresh_cookie(response, tokens.refresh_token)

    return TokenResponse(
        access_token=tokens.access_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(
        request: Request,
        response: Response,
        db: Session = Depends(get_db),
):
    _require_allowed_origin(request)
    raw_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if not raw_token:
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh session is unavailable.")
    try:
        _user, tokens = rotate_refresh_session(db, raw_token)
    except (InvalidRefreshSessionError, InactiveRefreshUserError):
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh session is invalid or expired.")

    _set_refresh_cookie(response, tokens.refresh_token)
    return TokenResponse(access_token=tokens.access_token, token_type="bearer")


@router.post("/logout")
def logout(
        request: Request,
        response: Response,
        db: Session = Depends(get_db),
):
    _require_allowed_origin(request)
    revoke_refresh_session(db, request.cookies.get(settings.REFRESH_COOKIE_NAME))
    _clear_refresh_cookie(response)
    return {"message": "Logged out successfully."}
