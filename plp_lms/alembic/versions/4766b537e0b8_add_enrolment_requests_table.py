"""add enrolment_requests table

Revision ID: 4766b537e0b8
Revises: d9f689d025ba
Create Date: 2026-06-14 12:00:25.884898

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4766b537e0b8'
down_revision: Union[str, Sequence[str], None] = 'd9f689d025ba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "enrolment_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("cohort_id", sa.Integer(), sa.ForeignKey("cohorts.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_enrolment_requests_id"), "enrolment_requests", ["id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_enrolment_requests_id"), table_name="enrolment_requests")
    op.drop_table("enrolment_requests")
