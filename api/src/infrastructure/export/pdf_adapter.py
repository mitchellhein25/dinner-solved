"""
Server-side PDF generation using fpdf2.
Produces three PDF types: grocery list, meal plan summary, individual recipe.
"""
from __future__ import annotations

from typing import List, Optional

from fpdf import FPDF

from domain.entities.grocery import GroceryListItem
from domain.entities.recipe import GroceryCategory, Recipe


CATEGORY_LABELS: dict[str, str] = {
    "produce": "Produce",
    "meat": "Meat",
    "dairy": "Dairy",
    "pantry": "Pantry",
    "frozen": "Frozen",
    "bakery": "Bakery",
    "other": "Other",
}

DAY_LABELS: dict[str, str] = {
    "mon": "Mon",
    "tue": "Tue",
    "wed": "Wed",
    "thu": "Thu",
    "fri": "Fri",
    "sat": "Sat",
    "sun": "Sun",
}

ACCENT = (79, 70, 229)   # indigo-600 (matches --accent CSS var)
INK = (30, 30, 30)
INK_LIGHT = (110, 110, 110)
WHITE = (255, 255, 255)

_UNICODE_MAP = {
    "\u2014": "--",   # em dash
    "\u2013": "-",    # en dash
    "\u2018": "'",    # left single quote
    "\u2019": "'",    # right single quote
    "\u201c": '"',    # left double quote
    "\u201d": '"',    # right double quote
    "\u2026": "...",  # ellipsis
    "\u00b7": "-",    # middle dot
    "\u2022": "-",    # bullet
}


def _safe(text: str) -> str:
    """Sanitise text for fpdf2 core (latin-1) fonts.

    Replaces common typographic characters with ASCII equivalents, then
    drops anything still outside latin-1 (e.g. emojis).
    """
    for char, replacement in _UNICODE_MAP.items():
        text = text.replace(char, replacement)
    return text.encode("latin-1", errors="ignore").decode("latin-1")


class _PDF(FPDF):
    """Base class with shared header / footer and helpers."""

    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(20, 20, 20)

    def header(self):
        pass  # custom headers per document type

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*INK_LIGHT)
        self.cell(0, 5, f"Page {self.page_no()}", align="C")

    def accent_bar(self, text: str, height: float = 10) -> None:
        """Full-width accent-coloured header bar."""
        self.set_fill_color(*ACCENT)
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 14)
        self.cell(0, height, _safe(text), ln=True, fill=True, align="L")
        self.ln(4)

    def section_title(self, text: str) -> None:
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*INK_LIGHT)
        self.set_fill_color(240, 240, 245)
        self.cell(0, 6, _safe(text).upper(), ln=True, fill=True)
        self.ln(1)

    def body_text(self, text: str, size: int = 10) -> None:
        self.set_font("Helvetica", "", size)
        self.set_text_color(*INK)
        self.multi_cell(0, 5, _safe(text))


# ---------------------------------------------------------------------------
# Grocery list PDF
# ---------------------------------------------------------------------------

def build_grocery_pdf(items: List[GroceryListItem], week_start_date: str) -> bytes:
    pdf = _PDF()
    pdf.add_page()

    pdf.accent_bar(f"Grocery List — Week of {week_start_date}")

    # Group by category
    groups: dict[str, List[GroceryListItem]] = {}
    for item in items:
        cat = item.category.value
        groups.setdefault(cat, []).append(item)

    category_order = ["produce", "meat", "dairy", "pantry", "bakery", "frozen", "other"]
    for cat in category_order:
        if cat not in groups:
            continue
        pdf.section_title(CATEGORY_LABELS.get(cat, cat))
        for item in groups[cat]:
            qty_str = f"{item.quantity:g} {item.unit}".strip()
            recipe_str = f"  ({', '.join(item.recipe_names)})" if item.recipe_names else ""
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*INK)
            # Name left, qty right
            pdf.cell(0, 6, _safe(f"{item.name}{recipe_str}"), ln=False)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_x(-40)
            pdf.cell(20, 6, _safe(qty_str), ln=True, align="R")
        pdf.ln(2)

    return bytes(pdf.output())


# ---------------------------------------------------------------------------
# Meal plan summary PDF
# ---------------------------------------------------------------------------

def build_plan_pdf(
    week_start_date: str,
    slot_recipe_pairs: List[tuple[str, str, List[str]]],  # (slot_name, recipe_name, days)
) -> bytes:
    """
    slot_recipe_pairs: list of (slot_name, recipe_name_with_emoji, day_labels)
    """
    pdf = _PDF()
    pdf.add_page()

    pdf.accent_bar(f"Meal Plan — Week of {week_start_date}")

    for slot_name, recipe_display, days in slot_recipe_pairs:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*INK)
        pdf.cell(0, 7, _safe(slot_name), ln=True)

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*INK_LIGHT)
        days_str = " / ".join(days)
        pdf.cell(0, 5, _safe(days_str), ln=True)

        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(*INK)
        pdf.cell(0, 6, _safe(recipe_display), ln=True)
        pdf.ln(3)

    return bytes(pdf.output())


# ---------------------------------------------------------------------------
# Individual recipe PDF
# ---------------------------------------------------------------------------

def build_recipe_pdf(recipe: Recipe) -> bytes:
    pdf = _PDF()
    pdf.add_page()

    # Title bar
    title = f"{recipe.emoji}  {recipe.name}"
    pdf.accent_bar(title, height=12)

    # Meta row
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*INK_LIGHT)
    meta_parts = [f"{recipe.prep_time} min prep"]
    if recipe.times_used:
        meta_parts.append(f"Used {recipe.times_used}x")
    if recipe.is_favorite:
        meta_parts.append("Favourite")
    pdf.cell(0, 5, _safe("  |  ".join(meta_parts)), ln=True)
    pdf.ln(3)

    # Key ingredients
    if recipe.key_ingredients:
        pdf.section_title("Key Ingredients")
        pdf.body_text(", ".join(recipe.key_ingredients))
        pdf.ln(3)

    # Full ingredient list grouped by category
    if recipe.ingredients:
        groups: dict[str, list] = {}
        for ing in recipe.ingredients:
            cat = ing.category.value
            groups.setdefault(cat, []).append(ing)

        pdf.section_title("Ingredients")
        category_order = ["produce", "meat", "dairy", "pantry", "bakery", "frozen", "other"]
        for cat in category_order:
            if cat not in groups:
                continue
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(*INK_LIGHT)
            pdf.cell(0, 5, _safe(CATEGORY_LABELS.get(cat, cat)), ln=True)
            for ing in groups[cat]:
                qty_str = f"{ing.quantity:g} {ing.unit}"
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(*INK)
                pdf.cell(40, 5, _safe(qty_str))
                pdf.cell(0, 5, _safe(ing.name), ln=True)
        pdf.ln(3)

    # Cooking instructions
    if recipe.cooking_instructions:
        pdf.section_title("Method")
        for i, step in enumerate(recipe.cooking_instructions, 1):
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*ACCENT)
            pdf.cell(8, 5, f"{i}.")
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*INK)
            pdf.multi_cell(0, 5, _safe(step))
            pdf.ln(1)
    else:
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(*INK_LIGHT)
        pdf.cell(0, 5, "Instructions not yet generated.", ln=True)

    return bytes(pdf.output())
