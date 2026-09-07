"""add attendance shift snapshot metrics

Revision ID: d7a8b9c0e1f2
Revises: cf0f501f17f7
Create Date: 2026-09-07 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d7a8b9c0e1f2"
down_revision: Union[str, Sequence[str], None] = "cf0f501f17f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "attendance",
        sa.Column("shift_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "attendance",
        sa.Column(
            "late_minutes",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "attendance",
        sa.Column(
            "early_leave_minutes",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "attendance",
        sa.Column(
            "working_minutes",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "attendance",
        sa.Column(
            "overtime_minutes",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.create_foreign_key(
        "fk_attendance_shift_id",
        "attendance",
        "shifts",
        ["shift_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_attendance_shift_id",
        "attendance",
        ["shift_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_attendance_shift_id", table_name="attendance")
    op.drop_constraint(
        "fk_attendance_shift_id",
        "attendance",
        type_="foreignkey",
    )
    op.drop_column("attendance", "overtime_minutes")
    op.drop_column("attendance", "working_minutes")
    op.drop_column("attendance", "early_leave_minutes")
    op.drop_column("attendance", "late_minutes")
    op.drop_column("attendance", "shift_id")