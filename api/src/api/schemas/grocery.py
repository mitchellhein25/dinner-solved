from pydantic import BaseModel


class GroceryListItemSchema(BaseModel):
    name: str
    quantity: float
    unit: str
    category: str
    recipe_names: list[str]


class GroceryListResponse(BaseModel):
    week_start_date: str
    items: list[GroceryListItemSchema]


class ExportRequest(BaseModel):
    week_start_date: str


class ExportResponse(BaseModel):
    result: str  # file path, URL, or confirmation string
