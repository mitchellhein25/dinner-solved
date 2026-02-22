from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from api.converters import recipe_to_detail, recipe_to_list_item
from api.dependencies import (
    HouseholdIdDep,
    get_delete_recipe,
    get_generate_instructions,
    get_get_recipe,
    get_list_recipes,
    get_toggle_favorite,
    get_update_recipe,
)
from infrastructure.export.pdf_adapter import build_recipe_pdf
from api.schemas.recipe import RecipeDetailSchema, RecipeListItemSchema
from application.use_cases.delete_recipe import DeleteRecipeUseCase
from application.use_cases.generate_instructions import GenerateInstructionsUseCase
from application.use_cases.get_recipe import GetRecipeUseCase
from application.use_cases.list_recipes import ListRecipesUseCase
from application.use_cases.toggle_favorite import ToggleFavoriteUseCase
from application.use_cases.update_recipe import UpdateRecipeUseCase

router = APIRouter()

ListRecipesDep = Annotated[ListRecipesUseCase, Depends(get_list_recipes)]
GetRecipeDep = Annotated[GetRecipeUseCase, Depends(get_get_recipe)]
ToggleFavoriteDep = Annotated[ToggleFavoriteUseCase, Depends(get_toggle_favorite)]
DeleteRecipeDep = Annotated[DeleteRecipeUseCase, Depends(get_delete_recipe)]
UpdateRecipeDep = Annotated[UpdateRecipeUseCase, Depends(get_update_recipe)]
GenerateInstructionsDep = Annotated[GenerateInstructionsUseCase, Depends(get_generate_instructions)]


class UpdateRecipeRequest(BaseModel):
    name: str
    emoji: str


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


@router.post("/{recipe_id}/instructions", response_model=RecipeDetailSchema)
async def generate_instructions(
    recipe_id: UUID,
    use_case: GenerateInstructionsDep,
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


@router.patch("/{recipe_id}", response_model=RecipeDetailSchema)
async def update_recipe(
    recipe_id: UUID,
    body: UpdateRecipeRequest,
    use_case: UpdateRecipeDep,
    household_id: HouseholdIdDep,
):
    try:
        recipe = await use_case.execute(recipe_id, name=body.name, emoji=body.emoji)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe_to_detail(recipe)


@router.delete("/{recipe_id}", status_code=204)
async def delete_recipe(
    recipe_id: UUID,
    use_case: DeleteRecipeDep,
    household_id: HouseholdIdDep,
):
    found = await use_case.execute(recipe_id)
    if not found:
        raise HTTPException(status_code=404, detail="Recipe not found")


@router.get("/{recipe_id}/export/pdf")
async def export_recipe_pdf(
    recipe_id: UUID,
    use_case: GetRecipeDep,
    household_id: HouseholdIdDep,
):
    recipe = await use_case.execute(recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    pdf_bytes = build_recipe_pdf(recipe)
    safe_name = recipe.name.lower().replace(" ", "-")[:40]
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="recipe-{safe_name}.pdf"'},
    )
