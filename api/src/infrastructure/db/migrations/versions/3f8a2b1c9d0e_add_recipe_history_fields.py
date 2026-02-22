"""add_recipe_history_fields

Revision ID: 3f8a2b1c9d0e
Revises: a1b2c3d4e5f6
Create Date: 2026-02-22

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY

revision: str = "3f8a2b1c9d0e"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add cooking_instructions (nullable — populated lazily on first detail view)
    op.add_column(
        "recipes",
        sa.Column("cooking_instructions", ARRAY(sa.String), nullable=True),
    )
    # Add usage tracking fields
    op.add_column(
        "recipes",
        sa.Column("times_used", sa.Integer, nullable=False, server_default="0"),
    )
    op.add_column(
        "recipes",
        sa.Column("last_used_at", sa.DateTime, nullable=True),
    )
    # Enforce unique (household_id, name) so upsert-by-name is safe
    op.create_unique_constraint(
        "uq_recipe_household_name",
        "recipes",
        ["household_id", "name"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_recipe_household_name", "recipes", type_="unique")
    op.drop_column("recipes", "last_used_at")
    op.drop_column("recipes", "times_used")
    op.drop_column("recipes", "cooking_instructions")
