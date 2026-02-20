from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from application.use_cases.manage_template import ManageTemplateUseCase
from api.converters import schema_to_template, template_to_schema
from api.dependencies import get_manage_template
from api.schemas.plan import MealPlanTemplateSchema, SaveTemplateRequest

router = APIRouter()

TemplateDep = Annotated[ManageTemplateUseCase, Depends(get_manage_template)]


@router.get("", response_model=MealPlanTemplateSchema)
async def get_template(use_case: TemplateDep):
    template = await use_case.get_template()
    if not template:
        raise HTTPException(status_code=404, detail="No template configured yet")
    return template_to_schema(template)


@router.post("", response_model=MealPlanTemplateSchema, status_code=status.HTTP_200_OK)
async def save_template(body: SaveTemplateRequest, use_case: TemplateDep):
    try:
        domain_template = schema_to_template(body.template)
        await use_case.save_template(domain_template)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return body.template
