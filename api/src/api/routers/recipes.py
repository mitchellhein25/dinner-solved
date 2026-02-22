from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from api.converters import recipe_to_detail, recipe_to_list_item
from api.dependencies import HouseholdIdDep, get_get_recipe, get_list_recipes, get_toggle_favorite
from api.schemas.recipe import RecipeDetailSchema, RecipeListItemSchema
from application.use_cases.get_recipe import GetRecipeUseCase
from application.use_cases.list_recipes import ListRecipesUseCase
from application.use_cases.toggle_favorite import ToggleFavoriteUseCase

router = APIRouter()

ListRecipesDep = Annotated[ListRecipesUseCase, Depends(get_list_recipes)]
GetRecipeDep = Annotated[GetRecipeUseCase, Depends(get_get_recipe)]
ToggleFavoriteDep = Annotated[ToggleFavoriteUseCase, Depends(get_toggle_favorite)]


@router.get("/", response_model=list[RecipeListItemSchema])
async def list_recipes(
    use_case: ListRecipesDep,
    household_id: HouseholdIdDep,
    sort: str = "recent",
    favorites_only: bool = False,
):
    recipes = await use_case.execute(sort=sort, favorites_only=favorites_only)
    return [recipe_to_list_item(r) for r in recipes]


@router.get("/{recipe_id}", response_model=RecipeDetailSchema)
async def get_recipe(
    recipe_id: UUID,
    use_case: GetRecipeDep,
    household_id: HouseholdIdDep,
):
    recipe = await use_case.execute(recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe_to_detail(recipe)


@router.patch("/{recipe_id}/favorite", response_model=RecipeDetailSchema)
async def toggle_favorite(
    recipe_id: UUID,
    use_case: ToggleFavoriteDep,
    household_id: HouseholdIdDep,
):
    recipe = await use_case.execute(recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe_to_detail(recipe)
