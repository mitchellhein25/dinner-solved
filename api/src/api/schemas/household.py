from uuid import UUID

from pydantic import BaseModel, Field


class HouseholdMemberSchema(BaseModel):
    id: UUID
    name: str
    emoji: str
    serving_size: float = Field(gt=0)

    model_config = {"from_attributes": True}


class SaveMembersRequest(BaseModel):
    members: list[HouseholdMemberSchema]


class MembersResponse(BaseModel):
    members: list[HouseholdMemberSchema]
