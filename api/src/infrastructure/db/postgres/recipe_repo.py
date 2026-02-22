from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.entities.recipe import GroceryCategory, Ingredient, Recipe
from domain.repositories.recipe_repository import RecipeRepository
from .models import IngredientRow, RecipeRow


class PostgresRecipeRepository(RecipeRepository):
    def __init__(self, session: AsyncSession, household_id: UUID):
        self._session = session
        self._household_id = household_id

    # ------------------------------------------------------------------
    # Save / upsert
    # ------------------------------------------------------------------

    async def save_recipe(self, recipe: Recipe) -> Recipe:
        """
        Upsert by UUID first, then fall back to name match within household.
        Returns the canonical Recipe (with the DB's authoritative id).
        """
        row = await self._find_row_by_id(recipe.id)
        if row is None:
            row = await self._find_row_by_name(recipe.name)

        if row is not None:
            # Update mutable fields; preserve canonical id and is_favorite
            row.emoji = recipe.emoji
            row.prep_time = recipe.prep_time
            row.key_ingredients = recipe.key_ingredients
            row.times_used = (row.times_used or 0) + 1
            row.last_used_at = datetime.utcnow()
            # Replace ingredients with latest from AI
            for ing in list(row.ingredients):
                await self._session.delete(ing)
            await self._session.flush()
            for ing in recipe.ingredients:
                row.ingredients.append(self._ingredient_row(ing))
            await self._session.flush()
            return self._to_entity(row)
        else:
            row = RecipeRow(
                id=recipe.id,
                household_id=self._household_id,
                name=recipe.name,
                emoji=recipe.emoji,
                prep_time=recipe.prep_time,
                key_ingredients=recipe.key_ingredients,
                is_favorite=recipe.is_favorite,
                source_url=recipe.source_url,
                times_used=1,
                last_used_at=datetime.utcnow(),
            )
            for ing in recipe.ingredients:
                row.ingredients.append(self._ingredient_row(ing))
            self._session.add(row)
            await self._session.flush()
            return self._to_entity(row)

    async def save_instructions(self, recipe_id: UUID, instructions: List[str]) -> None:
        row = await self._find_row_by_id(recipe_id)
        if row is not None:
            row.cooking_instructions = instructions
            await self._session.flush()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def get_recipes(
        self,
        sort: str = "recent",
        favorites_only: bool = False,
    ) -> List[Recipe]:
        stmt = (
            select(RecipeRow)
            .where(
                RecipeRow.household_id == self._household_id,
                RecipeRow.is_deleted.is_(False),
            )
            .options(selectinload(RecipeRow.ingredients))
        )
        if favorites_only:
            stmt = stmt.where(RecipeRow.is_favorite.is_(True))

        if sort == "most_used":
            stmt = stmt.order_by(RecipeRow.times_used.desc(), RecipeRow.name.asc())
        elif sort == "alpha":
            stmt = stmt.order_by(RecipeRow.name.asc())
        elif sort == "favorites_first":
            stmt = stmt.order_by(
                RecipeRow.is_favorite.desc(),
                RecipeRow.last_used_at.desc().nulls_last(),
            )
        else:  # "recent" (default)
            stmt = stmt.order_by(RecipeRow.last_used_at.desc().nulls_last())

        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]

    async def get_recipe(self, recipe_id: UUID) -> Optional[Recipe]:
        row = await self._find_row_by_id(recipe_id)
        return self._to_entity(row) if row else None

    async def get_recent_recipe_names(self, days: int = 14) -> List[str]:
        # Use naive UTC to match the TIMESTAMP WITHOUT TIME ZONE column type
        since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
        result = await self._session.execute(
            select(RecipeRow.name)
            .where(
                RecipeRow.household_id == self._household_id,
                RecipeRow.last_used_at >= since,
                RecipeRow.is_deleted.is_(False),
            )
            .order_by(RecipeRow.last_used_at.desc())
        )
        return list(result.scalars().all())

    async def toggle_favorite(self, recipe_id: UUID) -> Optional[Recipe]:
        row = await self._find_row_by_id(recipe_id)
        if row is None:
            return None
        row.is_favorite = not row.is_favorite
        await self._session.flush()
        return self._to_entity(row)

    async def delete_recipe(self, recipe_id: UUID) -> bool:
        row = await self._find_row_by_id(recipe_id)
        if row is None:
            return False
        row.is_deleted = True
        await self._session.flush()
        return True

    async def update_recipe(self, recipe_id: UUID, name: str, emoji: str) -> Optional[Recipe]:
        row = await self._find_row_by_id(recipe_id)
        if row is None:
            return None
        if row.name != name:
            # Check for name collision with another recipe in this household
            existing = await self._find_row_by_name(name)
            if existing is not None and existing.id != recipe_id:
                raise ValueError(f"A recipe named '{name}' already exists.")
        row.name = name
        row.emoji = emoji
        await self._session.flush()
        return self._to_entity(row)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _find_row_by_id(self, recipe_id: UUID) -> Optional[RecipeRow]:
        result = await self._session.execute(
            select(RecipeRow)
            .where(
                RecipeRow.id == recipe_id,
                RecipeRow.household_id == self._household_id,
            )
            .options(selectinload(RecipeRow.ingredients))
        )
        return result.scalar_one_or_none()

    async def _find_row_by_name(self, name: str) -> Optional[RecipeRow]:
        result = await self._session.execute(
            select(RecipeRow)
            .where(
                RecipeRow.name == name,
                RecipeRow.household_id == self._household_id,
            )
            .options(selectinload(RecipeRow.ingredients))
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _ingredient_row(ing: Ingredient) -> IngredientRow:
        return IngredientRow(
            id=uuid4(),
            name=ing.name,
            quantity=ing.quantity,
            unit=ing.unit,
            category=ing.category.value,
        )

    @staticmethod
    def _to_entity(row: RecipeRow) -> Recipe:
        return Recipe(
            id=row.id,
            name=row.name,
            emoji=row.emoji,
            prep_time=row.prep_time,
            key_ingredients=list(row.key_ingredients),
            is_favorite=row.is_favorite,
            source_url=row.source_url,
            cooking_instructions=list(row.cooking_instructions) if row.cooking_instructions else None,
            times_used=row.times_used or 0,
            last_used_at=row.last_used_at,
            ingredients=[
                Ingredient(
                    name=ing.name,
                    quantity=ing.quantity,
                    unit=ing.unit,
                    category=GroceryCategory(ing.category),
                )
                for ing in row.ingredients
            ],
        )
