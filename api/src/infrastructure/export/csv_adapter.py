import csv
import io
from typing import List

from application.ports.export_port import ExportPort
from domain.entities.grocery import GroceryListItem


class CsvExportAdapter(ExportPort):
    """
    Returns the grocery list as a CSV string.
    Groups items by category with a blank separator row between groups.
    """

    async def export(self, items: List[GroceryListItem], week_start_date: str) -> str:
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["Grocery List", f"Week of {week_start_date}"])
        writer.writerow([])
        writer.writerow(["Category", "Item", "Quantity", "Unit", "Recipes"])

        current_category = None
        for item in items:
            if item.category != current_category:
                if current_category is not None:
                    writer.writerow([])  # blank row between categories
                current_category = item.category
                writer.writerow([item.category.value.upper()])

            writer.writerow([
                "",
                item.name,
                item.quantity,
                item.unit,
                ", ".join(item.recipe_names),
            ])

        return output.getvalue()
