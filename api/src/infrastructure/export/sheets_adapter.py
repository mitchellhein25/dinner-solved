"""
Google Sheets export adapter.

Writes the grocery list to a Google Spreadsheet, creating it fresh each week
(or clearing the existing one if it already exists with that title).

Credentials are read from the environment:
  GOOGLE_SERVICE_ACCOUNT_JSON  – full service-account JSON as a string
  GOOGLE_SERVICE_ACCOUNT_PATH  – path to a service-account JSON file

Optionally, set GOOGLE_SHARE_EMAIL to share the resulting sheet with a user.
"""
import json
import os
from typing import List

import gspread

from application.ports.export_port import ExportPort
from domain.entities.grocery import GroceryListItem


class GoogleSheetsAdapter(ExportPort):
    """
    Exports the grocery list to a Google Sheet using a service account.
    Returns the URL of the created / updated spreadsheet.
    """

    def __init__(self, share_email: str | None = None) -> None:
        self._share_email = share_email

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_client(self) -> gspread.Client:
        sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
        sa_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_PATH")

        if sa_json:
            return gspread.service_account_from_dict(json.loads(sa_json))
        if sa_path:
            return gspread.service_account(filename=sa_path)

        raise RuntimeError(
            "Google Sheets credentials not configured. "
            "Set GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_SERVICE_ACCOUNT_PATH."
        )

    def _build_rows(
        self, items: List[GroceryListItem], week_start_date: str
    ) -> list[list[str]]:
        rows: list[list[str]] = [
            [f"Grocery List – Week of {week_start_date}"],
            [],
            ["Category", "Item", "Quantity", "Unit", "Recipes"],
        ]

        current_category = None
        for item in items:
            if item.category != current_category:
                if current_category is not None:
                    rows.append([])  # blank separator between categories
                current_category = item.category
                rows.append([item.category.value.upper()])

            rows.append([
                "",
                item.name,
                str(item.quantity),
                item.unit,
                ", ".join(item.recipe_names),
            ])

        return rows

    # ------------------------------------------------------------------
    # ExportPort implementation
    # ------------------------------------------------------------------

    async def export(self, items: List[GroceryListItem], week_start_date: str) -> str:
        client = self._get_client()
        title = f"Dinner Solved – Week of {week_start_date}"

        # Re-use an existing spreadsheet with the same title, or create one.
        try:
            spreadsheet = client.open(title)
            worksheet = spreadsheet.get_worksheet(0)
            worksheet.clear()
        except gspread.SpreadsheetNotFound:
            spreadsheet = client.create(title)
            worksheet = spreadsheet.get_worksheet(0)

        if self._share_email:
            spreadsheet.share(self._share_email, perm_type="user", role="writer")

        rows = self._build_rows(items, week_start_date)
        worksheet.update(rows)

        # Basic formatting: bold title and header row
        worksheet.format("A1", {"textFormat": {"bold": True, "fontSize": 14}})
        worksheet.format("A3:E3", {"textFormat": {"bold": True}})

        return spreadsheet.url
