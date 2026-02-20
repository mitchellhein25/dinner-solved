from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from domain.repositories.preference_repository import PreferenceRepository
from api.converters import prefs_to_schema, schema_to_prefs
from api.dependencies import get_preference_repo
from api.schemas.preferences import PreferencesSchema, SavePreferencesRequest
from infrastructure.db.postgres.preference_repo import PostgresPreferenceRepository

router = APIRouter()

PrefsDep = Annotated[PostgresPreferenceRepository, Depends(get_preference_repo)]


@router.get("", response_model=PreferencesSchema)
async def get_preferences(repo: PrefsDep):
    prefs = await repo.get_preferences()
    if not prefs:
        raise HTTPException(status_code=404, detail="No preferences saved yet")
    return prefs_to_schema(prefs)


@router.post("", response_model=PreferencesSchema)
async def save_preferences(body: SavePreferencesRequest, repo: PrefsDep):
    domain_prefs = schema_to_prefs(body.preferences)
    await repo.save_preferences(domain_prefs)
    return body.preferences
