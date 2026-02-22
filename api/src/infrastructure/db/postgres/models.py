"""
SQLAlchemy ORM models — the infrastructure concern only.
Domain entities never import from this module.
"""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class HouseholdRow(Base):
    __tablename__ = "households"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    email = Column(String(254), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class MagicLinkTokenRow(Base):
    __tablename__ = "magic_link_tokens"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    household_id = Column(PG_UUID(as_uuid=True), ForeignKey("households.id"), nullable=False)
    token = Column(PG_UUID(as_uuid=True), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)


# ---------------------------------------------------------------------------
# Household
# ---------------------------------------------------------------------------

class HouseholdMemberRow(Base):
    __tablename__ = "household_members"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    household_id = Column(PG_UUID(as_uuid=True), ForeignKey("households.id"), nullable=False)
    name = Column(String(100), nullable=False)
    emoji = Column(String(10), nullable=False)
    serving_size = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# ---------------------------------------------------------------------------
# Template
# ---------------------------------------------------------------------------

class MealPlanTemplateRow(Base):
    __tablename__ = "meal_plan_templates"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    household_id = Column(PG_UUID(as_uuid=True), ForeignKey("households.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    slots = relationship("MealSlotRow", back_populates="template", cascade="all, delete-orphan")


class MealSlotRow(Base):
    __tablename__ = "meal_slots"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    template_id = Column(PG_UUID(as_uuid=True), ForeignKey("meal_plan_templates.id"), nullable=False)
    name = Column(String(100), nullable=False)
    meal_type = Column(String(20), nullable=False)
    days = Column(ARRAY(String), nullable=False)  # ['mon', 'tue', ...]
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    template = relationship("MealPlanTemplateRow", back_populates="slots")
    slot_members = relationship("MealSlotMemberRow", back_populates="slot", cascade="all, delete-orphan")


class MealSlotMemberRow(Base):
    __tablename__ = "meal_slot_members"
    __table_args__ = (UniqueConstraint("slot_id", "member_id"),)

    slot_id = Column(PG_UUID(as_uuid=True), ForeignKey("meal_slots.id"), primary_key=True)
    member_id = Column(PG_UUID(as_uuid=True), primary_key=True)

    slot = relationship("MealSlotRow", back_populates="slot_members")


# ---------------------------------------------------------------------------
# Plans
# ---------------------------------------------------------------------------

class WeeklyPlanRow(Base):
    __tablename__ = "weekly_plans"
    __table_args__ = (UniqueConstraint("household_id", "week_start_date"),)

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    household_id = Column(PG_UUID(as_uuid=True), ForeignKey("households.id"), nullable=False)
    week_start_date = Column(String(10), nullable=False)  # 'YYYY-MM-DD'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    assignments = relationship("SlotAssignmentRow", back_populates="plan", cascade="all, delete-orphan")


class SlotAssignmentRow(Base):
    __tablename__ = "slot_assignments"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    plan_id = Column(PG_UUID(as_uuid=True), ForeignKey("weekly_plans.id"), nullable=False)
    slot_id = Column(PG_UUID(as_uuid=True), nullable=False)
    recipe_id = Column(PG_UUID(as_uuid=True), nullable=False)

    plan = relationship("WeeklyPlanRow", back_populates="assignments")


# ---------------------------------------------------------------------------
# Recipes
# ---------------------------------------------------------------------------

class RecipeRow(Base):
    __tablename__ = "recipes"
    __table_args__ = (
        UniqueConstraint("household_id", "name", name="uq_recipe_household_name"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    household_id = Column(PG_UUID(as_uuid=True), ForeignKey("households.id"), nullable=False)
    name = Column(String(200), nullable=False)
    emoji = Column(String(10), nullable=False)
    prep_time = Column(Integer, nullable=False)
    key_ingredients = Column(ARRAY(String), nullable=False)
    is_favorite = Column(Boolean, default=False, nullable=False)
    source_url = Column(Text, nullable=True)
    cooking_instructions = Column(ARRAY(String), nullable=True)
    times_used = Column(Integer, default=0, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    ingredients = relationship("IngredientRow", back_populates="recipe", cascade="all, delete-orphan")


class IngredientRow(Base):
    __tablename__ = "ingredients"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    recipe_id = Column(PG_UUID(as_uuid=True), ForeignKey("recipes.id"), nullable=False)
    name = Column(String(200), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    category = Column(String(20), nullable=False)

    recipe = relationship("RecipeRow", back_populates="ingredients")


# ---------------------------------------------------------------------------
# Preferences
# ---------------------------------------------------------------------------

class UserPreferencesRow(Base):
    __tablename__ = "user_preferences"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    household_id = Column(PG_UUID(as_uuid=True), ForeignKey("households.id"), nullable=False, unique=True)
    liked_ingredients = Column(ARRAY(String), nullable=False, default=list)
    disliked_ingredients = Column(ARRAY(String), nullable=False, default=list)
    cuisine_preferences = Column(ARRAY(String), nullable=False, default=list)
