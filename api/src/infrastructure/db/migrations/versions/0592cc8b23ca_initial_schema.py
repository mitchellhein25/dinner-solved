"""initial_schema

Revision ID: 0592cc8b23ca
Revises:
Create Date: 2026-02-19

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY, UUID

# revision identifiers, used by Alembic.
revision: str = "0592cc8b23ca"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Household
    # ------------------------------------------------------------------
    op.create_table(
        "household_members",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("emoji", sa.String(10), nullable=False),
        sa.Column("serving_size", sa.Float, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # ------------------------------------------------------------------
    # Template
    # ------------------------------------------------------------------
    op.create_table(
        "meal_plan_templates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "meal_slots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "template_id",
            UUID(as_uuid=True),
            sa.ForeignKey("meal_plan_templates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("meal_type", sa.String(20), nullable=False),
        sa.Column("days", ARRAY(sa.String), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "meal_slot_members",
        sa.Column(
            "slot_id",
            UUID(as_uuid=True),
            sa.ForeignKey("meal_slots.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("member_id", UUID(as_uuid=True), primary_key=True),
        sa.UniqueConstraint("slot_id", "member_id", name="uq_meal_slot_members"),
    )

    # ------------------------------------------------------------------
    # Recipes
    # ------------------------------------------------------------------
    op.create_table(
        "recipes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("emoji", sa.String(10), nullable=False),
        sa.Column("prep_time", sa.Integer, nullable=False),
        sa.Column("key_ingredients", ARRAY(sa.String), nullable=False),
        sa.Column("is_favorite", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("source_url", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "ingredients",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "recipe_id",
            UUID(as_uuid=True),
            sa.ForeignKey("recipes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("quantity", sa.Float, nullable=False),
        sa.Column("unit", sa.String(50), nullable=False),
        sa.Column("category", sa.String(20), nullable=False),
    )

    # ------------------------------------------------------------------
    # Plans
    # ------------------------------------------------------------------
    op.create_table(
        "weekly_plans",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("week_start_date", sa.String(10), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "slot_assignments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "plan_id",
            UUID(as_uuid=True),
            sa.ForeignKey("weekly_plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("slot_id", UUID(as_uuid=True), nullable=False),
        sa.Column("recipe_id", UUID(as_uuid=True), nullable=False),
    )

    # ------------------------------------------------------------------
    # Preferences
    # ------------------------------------------------------------------
    op.create_table(
        "user_preferences",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "liked_ingredients", ARRAY(sa.String), nullable=False, server_default="{}"
        ),
        sa.Column(
            "disliked_ingredients",
            ARRAY(sa.String),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "cuisine_preferences",
            ARRAY(sa.String),
            nullable=False,
            server_default="{}",
        ),
    )


def downgrade() -> None:
    op.drop_table("user_preferences")
    op.drop_table("slot_assignments")
    op.drop_table("weekly_plans")
    op.drop_table("ingredients")
    op.drop_table("recipes")
    op.drop_table("meal_slot_members")
    op.drop_table("meal_slots")
    op.drop_table("meal_plan_templates")
    op.drop_table("household_members")
