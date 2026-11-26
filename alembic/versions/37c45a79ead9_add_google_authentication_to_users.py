"""add google authentication to users

Revision ID: 37c45a79ead9
Revises: f95660151136
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "37c45a79ead9"
down_revision: Union[str, Sequence[str], None] = "f95660151136"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add Google's stable account identifier.
    op.add_column(
        "users",
        sa.Column("google_sub", sa.String(length=255), nullable=True),
    )

    # Passwords are optional for Google-only accounts.
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.VARCHAR(length=255),
        nullable=True,
    )

    # A Google identity can belong to only one user.
    op.create_unique_constraint(
        "uq_users_google_sub",
        "users",
        ["google_sub"],
    )

    # Every account must have at least one authentication method.
    op.create_check_constraint(
        "ck_users_has_auth_method",
        "users",
        "password_hash IS NOT NULL OR google_sub IS NOT NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_users_has_auth_method",
        "users",
        type_="check",
    )

    op.drop_constraint(
        "uq_users_google_sub",
        "users",
        type_="unique",
    )

    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.VARCHAR(length=255),
        nullable=False,
    )

    op.drop_column("users", "google_sub")