"""create notification center

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-09-08 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "f2a3b4c5d6e7"
down_revision: Union[str, Sequence[str], None] = "e1f2a3b4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    notification_type = postgresql.ENUM("CHECK_IN_REMINDER", "CHECK_IN_MISSING", "LATE_CHECK_IN", "CHECK_IN_SUCCESS", "CHECK_OUT_REMINDER", "CHECK_OUT_MISSING", "CHECK_OUT_SUCCESS", "LEAVE_APPROVED", "LEAVE_REJECTED", "OT_PENDING", "OT_APPROVED", "OT_REJECTED", "ATTENDANCE_ANOMALY", name="notification_type", create_type=False)
    notification_severity = postgresql.ENUM("INFO", "WARNING", "URGENT", "SUCCESS", name="notification_severity", create_type=False)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE notification_type AS ENUM (
                'CHECK_IN_REMINDER', 'CHECK_IN_MISSING', 'LATE_CHECK_IN', 'CHECK_IN_SUCCESS',
                'CHECK_OUT_REMINDER', 'CHECK_OUT_MISSING', 'CHECK_OUT_SUCCESS',
                'LEAVE_APPROVED', 'LEAVE_REJECTED', 'OT_PENDING', 'OT_APPROVED', 'OT_REJECTED',
                'ATTENDANCE_ANOMALY'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE notification_severity AS ENUM ('INFO', 'WARNING', 'URGENT', 'SUCCESS');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.create_table("notifications", sa.Column("id", sa.Integer(), autoincrement=True, nullable=False), sa.Column("employee_id", sa.Integer(), nullable=False), sa.Column("notification_type", notification_type, nullable=False), sa.Column("severity", notification_severity, nullable=False), sa.Column("attendance_date", sa.Date(), nullable=False), sa.Column("title", sa.String(length=120), nullable=False), sa.Column("message", sa.Text(), nullable=False), sa.Column("action_label", sa.String(length=80), nullable=True), sa.Column("action_path", sa.String(length=255), nullable=True), sa.Column("is_read", sa.Boolean(), server_default=sa.text("false"), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("read_at", sa.DateTime(timezone=True), nullable=True), sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True), sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("employee_id", "notification_type", "attendance_date", name="uq_notification_employee_type_date"))
    op.create_index("ix_notifications_id", "notifications", ["id"])
    op.create_index("ix_notifications_employee_id", "notifications", ["employee_id"])


def downgrade() -> None:
    op.drop_index("ix_notifications_employee_id", table_name="notifications")
    op.drop_index("ix_notifications_id", table_name="notifications")
    op.drop_table("notifications")
    sa.Enum(name="notification_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="notification_severity").drop(op.get_bind(), checkfirst=True)