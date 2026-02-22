from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from application.use_cases.build_grocery_list import BuildGroceryListUseCase
from api.converters import grocery_item_to_schema
from api.dependencies import get_build_grocery_list, get_csv_adapter, get_sheets_adapter
from api.schemas.grocery import ExportRequest, ExportResponse, GroceryListResponse
from infrastructure.export.csv_adapter import CsvExportAdapter
from infrastructure.export.pdf_adapter import build_grocery_pdf
from infrastructure.export.sheets_adapter import GoogleSheetsAdapter

router = APIRouter()

GroceryDep = Annotated[BuildGroceryListUseCase, Depends(get_build_grocery_list)]
CsvDep = Annotated[CsvExportAdapter, Depends(get_csv_adapter)]
SheetsDep = Annotated[GoogleSheetsAdapter, Depends(get_sheets_adapter)]


@router.get("/{week_start_date}", response_model=GroceryListResponse)
async def get_grocery_list(week_start_date: str, use_case: GroceryDep):
    try:
        items = await use_case.execute(week_start_date)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return GroceryListResponse(
        week_start_date=week_start_date,
        items=[grocery_item_to_schema(i) for i in items],
    )


@router.get("/{week_start_date}/export/pdf")
async def export_grocery_pdf(week_start_date: str, use_case: GroceryDep):
    try:
        items = await use_case.execute(week_start_date)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    pdf_bytes = build_grocery_pdf(items, week_start_date)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="grocery-{week_start_date}.pdf"'},
    )


@router.post("/export/csv", response_model=ExportResponse)
async def export_csv(body: ExportRequest, use_case: GroceryDep, csv_adapter: CsvDep):
    try:
        items = await use_case.execute(body.week_start_date)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    result = await csv_adapter.export(items, body.week_start_date)
    return ExportResponse(result=result)


@router.post("/export/sheets", response_model=ExportResponse)
async def export_sheets(
    body: ExportRequest, use_case: GroceryDep, sheets_adapter: SheetsDep
):
    try:
        items = await use_case.execute(body.week_start_date)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    try:
        result = await sheets_adapter.export(items, body.week_start_date)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return ExportResponse(result=result)
