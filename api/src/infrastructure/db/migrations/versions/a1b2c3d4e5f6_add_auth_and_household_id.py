"""add_auth_and_household_id

Revision ID: a1b2c3d4e5f6
Revises: 0592cc8b23ca
Create Date: 2026-02-20

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "0592cc8b23ca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Create households table
    # ------------------------------------------------------------------
    op.create_table(
        "households",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # ------------------------------------------------------------------
    # 2. Create magic_link_tokens table
    # ------------------------------------------------------------------
    op.create_table(
        "magic_link_tokens",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "household_id",
            UUID(as_uuid=True),
            sa.ForeignKey("households.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token", UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime, nullable=False),
        sa.Column("used_at", sa.DateTime, nullable=True),
    )

    # ------------------------------------------------------------------
    # 3. Truncate all existing tables (dev clean slate)
    # ------------------------------------------------------------------
    op.execute("TRUNCATE TABLE slot_assignments CASCADE")
    op.execute("TRUNCATE TABLE weekly_plans CASCADE")
    op.execute("TRUNCATE TABLE meal_slot_members CASCADE")
    op.execute("TRUNCATE TABLE meal_slots CASCADE")
    op.execute("TRUNCATE TABLE meal_plan_templates CASCADE")
    op.execute("TRUNCATE TABLE ingredients CASCADE")
    op.execute("TRUNCATE TABLE recipes CASCADE")
    op.execute("TRUNCATE TABLE user_preferences CASCADE")
    op.execute("TRUNCATE TABLE household_members CASCADE")

    # ------------------------------------------------------------------
    # 4. Add household_id FK to the 5 top-level tables
    # ------------------------------------------------------------------
    op.add_column(
        "household_members",
        sa.Column(
            "household_id",
            UUID(as_uuid=True),
            sa.ForeignKey("households.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )

    op.add_column(
        "meal_plan_templates",
        sa.Column(
            "household_id",
            UUID(as_uuid=True),
            sa.ForeignKey("households.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )

    op.add_column(
        "recipes",
        sa.Column(
            "household_id",
            UUID(as_uuid=True),
            sa.ForeignKey("households.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )

    op.add_column(
        "user_preferences",
        sa.Column(
            "household_id",
            UUID(as_uuid=True),
            sa.ForeignKey("households.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
    )

    op.add_column(
        "weekly_plans",
        sa.Column(
            "household_id",
            UUID(as_uuid=True),
            sa.ForeignKey("households.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )

    # ------------------------------------------------------------------
    # 5. Fix weekly_plans unique constraint
    # ------------------------------------------------------------------
    # Drop the old single-column unique constraint on week_start_date
    op.drop_constraint("weekly_plans_week_start_date_key", "weekly_plans", type_="unique")
    # Add composite unique (household_id, week_start_date)
    op.create_unique_constraint(
        "uq_weekly_plans_household_week",
        "weekly_plans",
        ["household_id", "week_start_date"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_weekly_plans_household_week", "weekly_plans", type_="unique")
    op.create_unique_constraint(
        "weekly_plans_week_start_date_key", "weekly_plans", ["week_start_date"]
    )

    op.drop_column("weekly_plans", "household_id")
    op.drop_column("user_preferences", "household_id")
    op.drop_column("recipes", "household_id")
    op.drop_column("meal_plan_templates", "household_id")
    op.drop_column("household_members", "household_id")

    op.drop_table("magic_link_tokens")
    op.drop_table("households")
