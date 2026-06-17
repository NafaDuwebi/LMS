"""add question_bank_options table

Revision ID: cbefad669181
Revises: e7ac184736bf
Create Date: 2026-06-14 12:34:07.522073

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cbefad669181'
down_revision: Union[str, Sequence[str], None] = 'e7ac184736bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "question_bank_options",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("bank_question_id", sa.Integer(), sa.ForeignKey("question_bank.id"), nullable=False),
        sa.Column("option_text", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), server_default="false"),
        sa.Column("option_label", sa.String(1), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_question_bank_options_id"), "question_bank_options", ["id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_question_bank_options_id"), table_name="question_bank_options")
    op.drop_table("question_bank_options")
