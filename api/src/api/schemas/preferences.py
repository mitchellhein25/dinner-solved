from uuid import UUID

from pydantic import BaseModel


class PreferencesSchema(BaseModel):
    id: UUID
    liked_ingredients: list[str] = []
    disliked_ingredients: list[str] = []
    cuisine_preferences: list[str] = []


class SavePreferencesRequest(BaseModel):
    preferences: PreferencesSchema
