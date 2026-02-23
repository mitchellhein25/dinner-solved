"""
Dependency injection — wires domain interfaces to concrete implementations.
Swap any implementation by changing only this file.
"""
import os
from typing import Annotated, AsyncGenerator, Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from application.use_cases.build_grocery_list import BuildGroceryListUseCase
from application.use_cases.confirm_plan import ConfirmPlanUseCase
from application.use_cases.create_recipe import CreateRecipeUseCase
from application.use_cases.delete_recipe import DeleteRecipeUseCase
from application.use_cases.full_update_recipe import FullUpdateRecipeUseCase
from application.use_cases.generate_instructions import GenerateInstructionsUseCase
from application.use_cases.get_recipe import GetRecipeUseCase
from application.use_cases.import_recipe import ImportRecipeUseCase
from application.use_cases.list_recipes import ListRecipesUseCase
from application.use_cases.manage_household import ManageHouseholdUseCase
from application.use_cases.manage_template import ManageTemplateUseCase
from application.use_cases.refine_recipes import RefineRecipesUseCase
from application.use_cases.suggest_recipes import SuggestRecipesUseCase
from application.use_cases.toggle_favorite import ToggleFavoriteUseCase
from application.use_cases.update_recipe import UpdateRecipeUseCase
from api.rate_limiter import RateLimiter
from domain.services.grocery_list_service import GroceryListService
from domain.services.meal_plan_service import MealPlanService
from domain.services.serving_calculator import ServingCalculator
from infrastructure.ai.claude_adapter import ClaudeAdapter
from infrastructure.db.postgres.auth_repo import AuthRepository
from infrastructure.db.postgres.database import get_session_factory
from infrastructure.db.postgres.household_repo import PostgresHouseholdRepository
from infrastructure.db.postgres.meal_plan_repo import (
    PostgresMealPlanTemplateRepository,
    PostgresWeeklyPlanRepository,
)
from infrastructure.db.postgres.preference_repo import PostgresPreferenceRepository
from infrastructure.db.postgres.recipe_repo import PostgresRecipeRepository
from infrastructure.export.csv_adapter import CsvExportAdapter
from infrastructure.export.sheets_adapter import GoogleSheetsAdapter


# ---------------------------------------------------------------------------
# DB session — one per request, auto-committed on success
# ---------------------------------------------------------------------------

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    async with factory() as session:
        async with session.begin():
            yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


# ---------------------------------------------------------------------------
# Auth dependencies
# ---------------------------------------------------------------------------

def get_auth_repo(session: SessionDep) -> AuthRepository:
    return AuthRepository(session)


async def get_household_id(
    session: SessionDep,
    x_household_id: Annotated[Optional[str], Header()] = None,
) -> UUID:
    if not x_household_id:
        raise HTTPException(status_code=401, detail="Missing X-Household-ID header")
    try:
        household_uuid = UUID(x_household_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid X-Household-ID format")
    auth_repo = AuthRepository(session)
    if not await auth_repo.household_exists(household_uuid):
        raise HTTPException(status_code=401, detail="Unknown household")
    return household_uuid


HouseholdIdDep = Annotated[UUID, Depends(get_household_id)]


# ---------------------------------------------------------------------------
# Repository dependencies
# ---------------------------------------------------------------------------

def get_household_repo(
    session: SessionDep,
    household_id: HouseholdIdDep,
) -> PostgresHouseholdRepository:
    return PostgresHouseholdRepository(session, household_id)


def get_recipe_repo(
    session: SessionDep,
    household_id: HouseholdIdDep,
) -> PostgresRecipeRepository:
    return PostgresRecipeRepository(session, household_id)


def get_template_repo(
    session: SessionDep,
    household_id: HouseholdIdDep,
) -> PostgresMealPlanTemplateRepository:
    return PostgresMealPlanTemplateRepository(session, household_id)


def get_plan_repo(
    session: SessionDep,
    household_id: HouseholdIdDep,
) -> PostgresWeeklyPlanRepository:
    return PostgresWeeklyPlanRepository(session, household_id)


def get_preference_repo(
    session: SessionDep,
    household_id: HouseholdIdDep,
) -> PostgresPreferenceRepository:
    return PostgresPreferenceRepository(session, household_id)


# ---------------------------------------------------------------------------
# Service / adapter singletons (stateless — safe to reuse across requests)
# ---------------------------------------------------------------------------

def get_ai_adapter() -> ClaudeAdapter:
    return ClaudeAdapter(api_key=os.environ["ANTHROPIC_API_KEY"])


def get_grocery_service() -> GroceryListService:
    return GroceryListService(serving_calculator=ServingCalculator())


def get_csv_adapter() -> CsvExportAdapter:
    return CsvExportAdapter()


def get_sheets_adapter() -> GoogleSheetsAdapter:
    share_email = os.environ.get("GOOGLE_SHARE_EMAIL")
    return GoogleSheetsAdapter(share_email=share_email)


# ---------------------------------------------------------------------------
# Rate limiter singleton
# ---------------------------------------------------------------------------

_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    return _rate_limiter


RateLimiterDep = Annotated[RateLimiter, Depends(get_rate_limiter)]


# ---------------------------------------------------------------------------
# Use case dependencies
# ---------------------------------------------------------------------------

def get_manage_household(
    household_repo: Annotated[PostgresHouseholdRepository, Depends(get_household_repo)],
) -> ManageHouseholdUseCase:
    return ManageHouseholdUseCase(household_repo=household_repo)


def get_manage_template(
    template_repo: Annotated[PostgresMealPlanTemplateRepository, Depends(get_template_repo)],
) -> ManageTemplateUseCase:
    return ManageTemplateUseCase(
        template_repo=template_repo,
        meal_plan_service=MealPlanService(),
    )


def get_suggest_recipes(
    template_repo: Annotated[PostgresMealPlanTemplateRepository, Depends(get_template_repo)],
    household_repo: Annotated[PostgresHouseholdRepository, Depends(get_household_repo)],
    preference_repo: Annotated[PostgresPreferenceRepository, Depends(get_preference_repo)],
    recipe_repo: Annotated[PostgresRecipeRepository, Depends(get_recipe_repo)],
) -> SuggestRecipesUseCase:
    return SuggestRecipesUseCase(
        ai_adapter=get_ai_adapter(),
        template_repo=template_repo,
        household_repo=household_repo,
        preference_repo=preference_repo,
        recipe_repo=recipe_repo,
    )


def get_refine_recipes(
    template_repo: Annotated[PostgresMealPlanTemplateRepository, Depends(get_template_repo)],
    household_repo: Annotated[PostgresHouseholdRepository, Depends(get_household_repo)],
    preference_repo: Annotated[PostgresPreferenceRepository, Depends(get_preference_repo)],
) -> RefineRecipesUseCase:
    return RefineRecipesUseCase(
        ai_adapter=get_ai_adapter(),
        template_repo=template_repo,
        household_repo=household_repo,
        preference_repo=preference_repo,
    )


def get_confirm_plan(
    plan_repo: Annotated[PostgresWeeklyPlanRepository, Depends(get_plan_repo)],
    recipe_repo: Annotated[PostgresRecipeRepository, Depends(get_recipe_repo)],
) -> ConfirmPlanUseCase:
    return ConfirmPlanUseCase(plan_repo=plan_repo, recipe_repo=recipe_repo)


def get_list_recipes(
    recipe_repo: Annotated[PostgresRecipeRepository, Depends(get_recipe_repo)],
) -> ListRecipesUseCase:
    return ListRecipesUseCase(recipe_repo=recipe_repo)


def get_get_recipe(
    recipe_repo: Annotated[PostgresRecipeRepository, Depends(get_recipe_repo)],
) -> GetRecipeUseCase:
    return GetRecipeUseCase(recipe_repo=recipe_repo)


def get_toggle_favorite(
    recipe_repo: Annotated[PostgresRecipeRepository, Depends(get_recipe_repo)],
) -> ToggleFavoriteUseCase:
    return ToggleFavoriteUseCase(recipe_repo=recipe_repo)


def get_delete_recipe(
    recipe_repo: Annotated[PostgresRecipeRepository, Depends(get_recipe_repo)],
) -> DeleteRecipeUseCase:
    return DeleteRecipeUseCase(recipe_repo=recipe_repo)


def get_update_recipe(
    recipe_repo: Annotated[PostgresRecipeRepository, Depends(get_recipe_repo)],
) -> UpdateRecipeUseCase:
    return UpdateRecipeUseCase(recipe_repo=recipe_repo)


def get_generate_instructions(
    recipe_repo: Annotated[PostgresRecipeRepository, Depends(get_recipe_repo)],
) -> GenerateInstructionsUseCase:
    return GenerateInstructionsUseCase(recipe_repo=recipe_repo, ai_port=get_ai_adapter())




def get_import_recipe() -> ImportRecipeUseCase:
    return ImportRecipeUseCase(ai_port=get_ai_adapter())


def get_create_recipe(
    recipe_repo: Annotated[PostgresRecipeRepository, Depends(get_recipe_repo)],
) -> CreateRecipeUseCase:
    return CreateRecipeUseCase(recipe_repo=recipe_repo)


def get_full_update_recipe(
    recipe_repo: Annotated[PostgresRecipeRepository, Depends(get_recipe_repo)],
) -> FullUpdateRecipeUseCase:
    return FullUpdateRecipeUseCase(recipe_repo=recipe_repo)


def get_build_grocery_list(
    plan_repo: Annotated[PostgresWeeklyPlanRepository, Depends(get_plan_repo)],
    template_repo: Annotated[PostgresMealPlanTemplateRepository, Depends(get_template_repo)],
    household_repo: Annotated[PostgresHouseholdRepository, Depends(get_household_repo)],
    recipe_repo: Annotated[PostgresRecipeRepository, Depends(get_recipe_repo)],
) -> BuildGroceryListUseCase:
    return BuildGroceryListUseCase(
        plan_repo=plan_repo,
        template_repo=template_repo,
        household_repo=household_repo,
        recipe_repo=recipe_repo,
        grocery_service=get_grocery_service(),
    )
