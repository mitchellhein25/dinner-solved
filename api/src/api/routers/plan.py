from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from application.use_cases.confirm_plan import ConfirmPlanUseCase
from application.use_cases.refine_recipes import RefineRecipesUseCase
from application.use_cases.suggest_recipes import RecipeSuggestion, SuggestRecipesUseCase
from api.converters import schema_to_recipe, schema_to_slot, suggestion_to_schema
from api.dependencies import get_confirm_plan, get_refine_recipes, get_suggest_recipes
from api.schemas.plan import (
    ConfirmRequest,
    RefineRequest,
    SuggestRequest,
    SuggestionsResponse,
    WeeklyPlanSchema,
)

router = APIRouter()

SuggestDep = Annotated[SuggestRecipesUseCase, Depends(get_suggest_recipes)]
RefineDep = Annotated[RefineRecipesUseCase, Depends(get_refine_recipes)]
ConfirmDep = Annotated[ConfirmPlanUseCase, Depends(get_confirm_plan)]


@router.post("/suggest", response_model=SuggestionsResponse)
async def suggest_recipes(body: SuggestRequest, use_case: SuggestDep):
    try:
        suggestions = await use_case.execute(week_context=body.week_context)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return SuggestionsResponse(suggestions=[suggestion_to_schema(s) for s in suggestions])


@router.post("/refine", response_model=SuggestionsResponse)
async def refine_recipes(body: RefineRequest, use_case: RefineDep):
    existing = {
        slot_id: schema_to_recipe(recipe_schema)
        for slot_id, recipe_schema in body.existing_assignments.items()
    }
    try:
        suggestions = await use_case.execute(
            existing_assignments=existing,
            user_message=body.user_message,
            slot_id_to_refine=body.slot_id_to_refine,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return SuggestionsResponse(suggestions=[suggestion_to_schema(s) for s in suggestions])


@router.post("/confirm", response_model=WeeklyPlanSchema)
async def confirm_plan(body: ConfirmRequest, use_case: ConfirmDep):
    suggestions = [
        RecipeSuggestion(
            slot=schema_to_slot(s.slot),
            recipe=schema_to_recipe(s.recipe),
        )
        for s in body.suggestions
    ]
    plan = await use_case.execute(
        week_start_date=body.week_start_date,
        suggestions=suggestions,
    )
    return WeeklyPlanSchema(
        id=plan.id,
        week_start_date=plan.week_start_date,
        assignments=[
            {"slot_id": str(a.slot_id), "recipe_id": str(a.recipe_id)}
            for a in plan.assignments
        ],
    )
