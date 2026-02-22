from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from application.use_cases.confirm_plan import ConfirmPlanUseCase
from application.use_cases.refine_recipes import RefineRecipesUseCase
from application.use_cases.suggest_recipes import RecipeSuggestion, SuggestRecipesUseCase
from api.converters import recipe_to_list_item, schema_to_recipe, schema_to_slot, slot_options_to_schema
from api.dependencies import (
    HouseholdIdDep,
    RateLimiterDep,
    get_confirm_plan,
    get_plan_repo,
    get_recipe_repo,
    get_refine_recipes,
    get_suggest_recipes,
    get_template_repo,
)
from api.schemas.plan import (
    ConfirmRequest,
    ConfirmedAssignmentSchema,
    ConfirmedPlanSchema,
    RefineRequest,
    RegenerateSlotRequest,
    SlotOptionsResponse,
    SuggestRequest,
    WeeklyPlanSchema,
)
from infrastructure.db.postgres.meal_plan_repo import PostgresMealPlanTemplateRepository, PostgresWeeklyPlanRepository
from infrastructure.db.postgres.recipe_repo import PostgresRecipeRepository
from infrastructure.export.pdf_adapter import DAY_LABELS, build_plan_pdf

router = APIRouter()

SuggestDep = Annotated[SuggestRecipesUseCase, Depends(get_suggest_recipes)]
RefineDep = Annotated[RefineRecipesUseCase, Depends(get_refine_recipes)]
ConfirmDep = Annotated[ConfirmPlanUseCase, Depends(get_confirm_plan)]
PlanRepoDep = Annotated[PostgresWeeklyPlanRepository, Depends(get_plan_repo)]
RecipeRepoDep = Annotated[PostgresRecipeRepository, Depends(get_recipe_repo)]
TemplateRepoDep = Annotated[PostgresMealPlanTemplateRepository, Depends(get_template_repo)]


def _rate_limit_error(remaining: float, resets_at: datetime | None) -> HTTPException:
    retry_after = 0
    if resets_at:
        retry_after = max(0, int((resets_at - datetime.now(timezone.utc)).total_seconds()))
    return HTTPException(
        status_code=429,
        detail={
            "reason": "Rate limit exceeded",
            "retry_after_seconds": retry_after,
            "budget_remaining": remaining,
        },
    )


@router.get("/{week_start_date}", response_model=ConfirmedPlanSchema)
async def get_confirmed_plan(
    week_start_date: str,
    plan_repo: PlanRepoDep,
    recipe_repo: RecipeRepoDep,
):
    plan = await plan_repo.get_plan(week_start_date)
    if plan is None:
        return ConfirmedPlanSchema(week_start_date=week_start_date, assignments=[])
    assignments = []
    for a in plan.assignments:
        recipe = await recipe_repo.get_recipe(a.recipe_id)
        if recipe:
            assignments.append(
                ConfirmedAssignmentSchema(slot_id=a.slot_id, recipe=recipe_to_list_item(recipe))
            )
    return ConfirmedPlanSchema(week_start_date=week_start_date, assignments=assignments)


@router.get("/{week_start_date}/export/pdf")
async def export_plan_pdf(
    week_start_date: str,
    plan_repo: PlanRepoDep,
    recipe_repo: RecipeRepoDep,
    template_repo: TemplateRepoDep,
):
    plan = await plan_repo.get_plan(week_start_date)
    if plan is None:
        raise HTTPException(status_code=404, detail="No confirmed plan for this week")

    template = await template_repo.get_template()

    # Build slot lookup: slot_id -> slot
    slot_map = {}
    if template:
        for slot in template.slots:
            slot_map[str(slot.id)] = slot

    pairs = []
    for a in plan.assignments:
        recipe = await recipe_repo.get_recipe(a.recipe_id)
        if recipe is None:
            continue
        slot = slot_map.get(str(a.slot_id))
        slot_name = slot.name if slot else "Meal"
        days = [DAY_LABELS.get(d.value, d.value) for d in slot.days] if slot else []
        recipe_display = f"{recipe.emoji}  {recipe.name}"
        pairs.append((slot_name, recipe_display, days))

    pdf_bytes = build_plan_pdf(week_start_date, pairs)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="meal-plan-{week_start_date}.pdf"'},
    )


@router.post("/suggest", response_model=SlotOptionsResponse)
async def suggest_recipes(
    body: SuggestRequest,
    use_case: SuggestDep,
    rate_limiter: RateLimiterDep,
    household_id: HouseholdIdDep,
):
    allowed, remaining, resets_at = await rate_limiter.check_and_consume(
        str(household_id), cost=1.0
    )
    if not allowed:
        raise _rate_limit_error(remaining, resets_at)

    try:
        slot_options = await use_case.execute(week_context=body.week_context)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return SlotOptionsResponse(
        slot_options=[slot_options_to_schema(so) for so in slot_options],
        budget_remaining=remaining,
        budget_resets_at=resets_at,
    )


@router.post("/refine", response_model=SlotOptionsResponse)
async def refine_recipes(
    body: RefineRequest,
    use_case: RefineDep,
    rate_limiter: RateLimiterDep,
    household_id: HouseholdIdDep,
):
    allowed, remaining, resets_at = await rate_limiter.check_and_consume(
        str(household_id), cost=1.0
    )
    if not allowed:
        raise _rate_limit_error(remaining, resets_at)

    existing = {
        slot_id: schema_to_recipe(recipe_schema)
        for slot_id, recipe_schema in body.existing_assignments.items()
    }
    try:
        slot_options = await use_case.execute(
            existing_assignments=existing,
            user_message=body.user_message,
            locked_slot_ids=body.locked_slot_ids,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return SlotOptionsResponse(
        slot_options=[slot_options_to_schema(so) for so in slot_options],
        budget_remaining=remaining,
        budget_resets_at=resets_at,
    )


@router.post("/suggest-slot", response_model=SlotOptionsResponse)
async def suggest_slot(
    body: RegenerateSlotRequest,
    use_case: SuggestDep,
    rate_limiter: RateLimiterDep,
    household_id: HouseholdIdDep,
):
    allowed, remaining, resets_at = await rate_limiter.check_and_consume(
        str(household_id), cost=0.5
    )
    if not allowed:
        raise _rate_limit_error(remaining, resets_at)

    existing_chosen = {
        slot_id: schema_to_recipe(recipe_schema)
        for slot_id, recipe_schema in body.existing_chosen.items()
    }
    try:
        slot_option = await use_case.execute_for_slot(
            slot_id=body.slot_id,
            existing_chosen=existing_chosen,
            week_context=body.week_context,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return SlotOptionsResponse(
        slot_options=[slot_options_to_schema(slot_option)],
        budget_remaining=remaining,
        budget_resets_at=resets_at,
    )


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
