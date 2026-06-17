"""change notification_preferences to Text

Revision ID: a1b2c3d4e5f6
Revises: cbefad669181
Create Date: 2026-06-14 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "cbefad669181"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("users", "notification_preferences",
                    existing_type=sa.String(50),
                    type_=sa.Text,
                    existing_nullable=True,
                    postgresql_using="notification_preferences::text")


def downgrade() -> None:
    op.alter_column("users", "notification_preferences",
                    existing_type=sa.Text,
                    type_=sa.String(50),
                    existing_nullable=True)
