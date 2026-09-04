"""add cascade delete to employee user foreign key

Revision ID: a2c4d6e8f901
Revises: fe1b7eb7c77b
Create Date: 2026-09-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a2c4d6e8f901"
down_revision: Union[str, Sequence[str], None] = "fe1b7eb7c77b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "employees_user_id_fkey",
        "employees",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "employees_user_id_fkey",
        "employees",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "employees_user_id_fkey",
        "employees",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "employees_user_id_fkey",
        "employees",
        "users",
        ["user_id"],
        ["id"],
    )
