"""add cascade delete to employee user foreign key

Revision ID: a2c4d6e8f901
Revises: fe1b7eb7c77b
Create Date: 2026-09-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a2c4d6e8f901"
down_revision: Union[str, Sequence[str], None] = "fe1b7eb7c77b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if op.get_bind().dialect.name == "sqlite":
        metadata = sa.MetaData()
        employees = sa.Table(
            "employees",
            metadata,
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("employee_code", sa.String(length=50), nullable=False),
            sa.Column("full_name", sa.String(length=100), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("department", sa.String(length=100), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("employee_code"),
            sa.UniqueConstraint("email"),
            sa.UniqueConstraint("user_id"),
        )

        with op.batch_alter_table(
            "employees",
            copy_from=employees,
            recreate="always",
        ) as batch_op:
            batch_op.create_foreign_key(
                "employees_user_id_fkey",
                "users",
                ["user_id"],
                ["id"],
                ondelete="CASCADE",
            )
        return

    with op.batch_alter_table("employees", recreate="always") as batch_op:
        batch_op.drop_constraint(
            "employees_user_id_fkey",
            type_="foreignkey",
        )
        batch_op.create_foreign_key(
            "employees_user_id_fkey",
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    with op.batch_alter_table("employees", recreate="always") as batch_op:
        batch_op.drop_constraint(
            "employees_user_id_fkey",
            type_="foreignkey",
        )
        batch_op.create_foreign_key(
            "employees_user_id_fkey",
            "users",
            ["user_id"],
            ["id"],
        )
