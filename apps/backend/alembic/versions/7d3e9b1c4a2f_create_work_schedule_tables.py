"""create work schedule tables

Revision ID: 7d3e9b1c4a2f
Revises: fe1b7eb7c77b
Create Date: 2026-09-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7d3e9b1c4a2f"
down_revision: Union[str, Sequence[str], None] = "fe1b7eb7c77b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "shifts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("break_start_time", sa.Time(), nullable=True),
        sa.Column("break_end_time", sa.Time(), nullable=True),
        sa.Column("late_tolerance_minutes", sa.Integer(), nullable=False),
        sa.Column("early_checkin_minutes", sa.Integer(), nullable=False),
        sa.Column("is_overnight", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        sa.CheckConstraint("late_tolerance_minutes >= 0", name="ck_shift_late_tolerance"),
        sa.CheckConstraint("early_checkin_minutes >= 0", name="ck_shift_early_checkin"),
    )
    op.create_index(op.f("ix_shifts_id"), "shifts", ["id"], unique=False)

    op.create_table(
        "work_schedules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_work_schedules_id"), "work_schedules", ["id"], unique=False)

    op.create_table(
        "schedule_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("schedule_id", sa.Integer(), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("shift_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["schedule_id"], ["work_schedules.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["shift_id"], ["shifts.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("schedule_id", "day_of_week", name="uq_schedule_rule_schedule_day"),
        sa.CheckConstraint("day_of_week >= 0 AND day_of_week <= 6", name="ck_schedule_rule_day"),
    )
    op.create_index(op.f("ix_schedule_rules_id"), "schedule_rules", ["id"], unique=False)

    op.create_table(
        "schedule_assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("schedule_id", sa.Integer(), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["schedule_id"], ["work_schedules.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="ck_schedule_assignment_effective_dates",
        ),
    )
    op.create_index(op.f("ix_schedule_assignments_id"), "schedule_assignments", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_schedule_assignments_id"), table_name="schedule_assignments")
    op.drop_table("schedule_assignments")
    op.drop_index(op.f("ix_schedule_rules_id"), table_name="schedule_rules")
    op.drop_table("schedule_rules")
    op.drop_index(op.f("ix_work_schedules_id"), table_name="work_schedules")
    op.drop_table("work_schedules")
    op.drop_index(op.f("ix_shifts_id"), table_name="shifts")
    op.drop_table("shifts")