from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from application.use_cases.manage_household import ManageHouseholdUseCase
from api.converters import member_to_schema, schema_to_member
from api.dependencies import get_manage_household
from api.schemas.household import HouseholdMemberSchema, MembersResponse, SaveMembersRequest

router = APIRouter()

HouseholdDep = Annotated[ManageHouseholdUseCase, Depends(get_manage_household)]


@router.get("/members", response_model=MembersResponse)
async def get_members(use_case: HouseholdDep):
    members = await use_case.get_members()
    return MembersResponse(members=[member_to_schema(m) for m in members])


@router.post("/members", response_model=MembersResponse, status_code=status.HTTP_200_OK)
async def save_members(body: SaveMembersRequest, use_case: HouseholdDep):
    members = [schema_to_member(s) for s in body.members]
    await use_case.save_members(members)
    return MembersResponse(members=body.members)


@router.get("/members/{member_id}", response_model=HouseholdMemberSchema)
async def get_member(member_id: UUID, use_case: HouseholdDep):
    member = await use_case.get_member(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member_to_schema(member)
