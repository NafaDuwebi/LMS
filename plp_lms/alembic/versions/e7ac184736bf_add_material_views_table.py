"""add material_views table

Revision ID: e7ac184736bf
Revises: 4766b537e0b8
Create Date: 2026-06-14 12:09:42.867858

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7ac184736bf'
down_revision: Union[str, Sequence[str], None] = '4766b537e0b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "material_views",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("material_id", sa.Integer(), sa.ForeignKey("materials.id"), nullable=False),
        sa.Column("viewed_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("view_duration_seconds", sa.Integer(), server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_material_views_id"), "material_views", ["id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_material_views_id"), table_name="material_views")
    op.drop_table("material_views")
