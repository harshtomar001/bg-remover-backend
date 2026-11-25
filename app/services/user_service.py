from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserUpdate


def get_user_profile(user: User) -> User:
    return user


def update_user_profile(
        db: Session,
        user: User,
        user_data: UserUpdate,
) -> User:

    user.name = user_data.name.strip()

    db.commit()
    db.refresh(user)

    return user


def delete_user_account(
        db: Session,
        user: User,
) -> None:

    db.delete(user)
    db.commit()