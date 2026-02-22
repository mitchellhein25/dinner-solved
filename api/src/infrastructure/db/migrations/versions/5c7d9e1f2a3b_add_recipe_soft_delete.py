"""add_recipe_soft_delete

Revision ID: 5c7d9e1f2a3b
Revises: 3f8a2b1c9d0e
Create Date: 2026-02-22

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5c7d9e1f2a3b"
down_revision: Union[str, None] = "3f8a2b1c9d0e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "recipes",
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )


def downgrade() -> None:
    op.drop_column("recipes", "is_deleted")
