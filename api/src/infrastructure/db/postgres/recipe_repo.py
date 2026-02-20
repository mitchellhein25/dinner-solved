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

    async def save_recipe(self, recipe: Recipe) -> None:
        # Upsert: delete existing then re-insert (simple and correct for this scale)
        existing = await self._session.execute(
            select(RecipeRow).where(
                RecipeRow.id == recipe.id,
                RecipeRow.household_id == self._household_id,
            )
        )
        existing_row = existing.scalar_one_or_none()
        if existing_row:
            await self._session.delete(existing_row)
            await self._session.flush()

        row = RecipeRow(
            id=recipe.id,
            household_id=self._household_id,
            name=recipe.name,
            emoji=recipe.emoji,
            prep_time=recipe.prep_time,
            key_ingredients=recipe.key_ingredients,
            is_favorite=recipe.is_favorite,
            source_url=recipe.source_url,
        )
        for ing in recipe.ingredients:
            row.ingredients.append(IngredientRow(
                id=uuid4(),
                name=ing.name,
                quantity=ing.quantity,
                unit=ing.unit,
                category=ing.category.value,
            ))
        self._session.add(row)
        await self._session.flush()

    async def get_recipes(self) -> List[Recipe]:
        result = await self._session.execute(
            select(RecipeRow)
            .where(RecipeRow.household_id == self._household_id)
            .options(selectinload(RecipeRow.ingredients))
        )
        return [self._to_entity(row) for row in result.scalars().all()]

    async def get_recipe(self, recipe_id: UUID) -> Optional[Recipe]:
        result = await self._session.execute(
            select(RecipeRow)
            .where(
                RecipeRow.id == recipe_id,
                RecipeRow.household_id == self._household_id,
            )
            .options(selectinload(RecipeRow.ingredients))
        )
        row = result.scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def get_favorites(self) -> List[Recipe]:
        result = await self._session.execute(
            select(RecipeRow)
            .where(
                RecipeRow.household_id == self._household_id,
                RecipeRow.is_favorite == True,
            )
            .options(selectinload(RecipeRow.ingredients))
        )
        return [self._to_entity(row) for row in result.scalars().all()]

    async def toggle_favorite(self, recipe_id: UUID) -> None:
        result = await self._session.execute(
            select(RecipeRow).where(
                RecipeRow.id == recipe_id,
                RecipeRow.household_id == self._household_id,
            )
        )
        row = result.scalar_one_or_none()
        if row:
            row.is_favorite = not row.is_favorite
            await self._session.flush()

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
