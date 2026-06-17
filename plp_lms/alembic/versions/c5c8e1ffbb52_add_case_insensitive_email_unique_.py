"""add case-insensitive email unique constraint

Revision ID: c5c8e1ffbb52
Revises: 7ed34e4a807a
Create Date: 2026-06-13 21:14:23.767202

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5c8e1ffbb52'
down_revision: Union[str, Sequence[str], None] = '7ed34e4a807a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the existing unique index on users.email (created by SQLAlchemy Column(unique=True))
    op.drop_index("ix_users_email", table_name="users")
    # Add a case-insensitive unique index on LOWER(email)
    op.create_index("uq_users_email_ci", "users", [sa.text("LOWER(email)")], unique=True)


def downgrade() -> None:
    op.drop_index("uq_users_email_ci", table_name="users")
    op.create_index("ix_users_email", "users", ["email"], unique=True)
