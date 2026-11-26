from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate
from app.schemas.auth import UserLogin
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)


class EmailAlreadyRegisteredError(Exception):
    """Raised when an email is already registered."""
    pass


class InvalidCredentialsError(Exception):
    """Raised when login credentials are invalid."""
    pass


def register_user(db: Session, user_data: UserCreate) -> User:
    """
    Register a new user.

    Returns the newly created User object.
    """

    email = str(user_data.email).strip().lower()

    # Check whether the email already exists.
    existing_user = db.scalar(
        select(User).where(User.email == email)
    )

    if existing_user:
        raise EmailAlreadyRegisteredError(
            "An account with this email already exists."
        )

    # Hash the password before storing it.
    hashed_password = hash_password(user_data.password)

    new_user = User(
        name=user_data.name.strip(),
        email=email,
        password_hash=hashed_password,
    )

    db.add(new_user)

    try:
        db.commit()
        db.refresh(new_user)

    except IntegrityError:
        db.rollback()

        # Handle concurrent registrations with the same email.
        existing_user = db.scalar(
            select(User).where(User.email == email)
        )

        if existing_user:
            raise EmailAlreadyRegisteredError(
                "An account with this email already exists."
            )

        raise

    return new_user


def authenticate_password_user(db: Session, credentials: UserLogin) -> User:
    """
    Authenticate a user and return the corresponding database user.

    Raises InvalidCredentialsError for invalid credentials
    or inactive accounts.
    """

    email = str(credentials.email).strip().lower()

    user = db.scalar(
        select(User).where(User.email == email)
    )

    # Use the same error for nonexistent users and wrong passwords.
    if not user:
        raise InvalidCredentialsError("Invalid email or password.")

# Google-only accounts cannot authenticate using passwords.
    if not user.password_hash:
        raise InvalidCredentialsError("Invalid email or password.")

    if not verify_password(
            credentials.password,
            user.password_hash,
    ):
        raise InvalidCredentialsError("Invalid email or password.")

    if not user.is_active:
        raise InvalidCredentialsError("Invalid email or password.")

    return user


def login_user(db: Session, credentials: UserLogin) -> str:
    """Backward-compatible helper retained for existing service callers."""
    user = authenticate_password_user(db, credentials)
    return create_access_token(str(user.id))
