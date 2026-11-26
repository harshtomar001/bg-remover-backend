from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User


class GoogleAccountConflictError(Exception):
    """Raised when the Google email belongs to another account."""


class GoogleAccountDisabledError(Exception):
    """Raised when the Google account is inactive."""


def authenticate_google_user(
    db: Session,
    google_sub: str,
    email: str,
    name: str | None,
) -> User:
    """
    Find an existing Google user or create a new one.

    Google identities are matched using Google's stable subject ID.
    Existing password accounts are never silently linked.
    """

    # 1. Look up the Google identity first.
    user = db.scalar(
        select(User).where(User.google_sub == google_sub)
    )

    if user:
        if not user.is_active:
            raise GoogleAccountDisabledError()

        return user

    # 2. Check whether the email already belongs to another account.
    existing_user = db.scalar(
        select(User).where(User.email == email)
    )

    if existing_user:
        raise GoogleAccountConflictError(
            "An account with this email already exists. "
            "Please sign in using your existing login method."
        )

    # 3. Create a new Google-only user.
    display_name = (name or "").strip() or email.split("@")[0]
    display_name = display_name[:100]

    new_user = User(
        name=display_name,
        email=email,
        password_hash=None,
        google_sub=google_sub,
    )

    db.add(new_user)

    try:
        db.commit()
        db.refresh(new_user)

    except IntegrityError:
        db.rollback()

        # Another request may have created this Google account
        # or registered the email concurrently.
        user = db.scalar(
            select(User).where(User.google_sub == google_sub)
        )

        if user:
            if not user.is_active:
                raise GoogleAccountDisabledError()

            return user

        existing_user = db.scalar(
            select(User).where(User.email == email)
        )

        if existing_user:
            raise GoogleAccountConflictError(
                "An account with this email already exists."
            )

        raise

    return new_user