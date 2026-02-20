import json
from typing import List
from uuid import uuid4

from anthropic import AsyncAnthropic

from application.ports.ai_port import AIPort, RefinementRequest, SuggestionRequest
from domain.entities.recipe import GroceryCategory, Ingredient, Recipe

# The model ID must match an available Claude model.
DEFAULT_MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a meal planning assistant for Dinner Solved.
When asked to suggest recipes, respond ONLY with a valid JSON array.
Each recipe must follow this exact structure:
{
  "name": "Recipe Name",
  "emoji": "🍝",
  "prep_time": 30,
  "key_ingredients": ["ingredient1", "ingredient2", "ingredient3"],
  "ingredients": [
    {
      "name": "ingredient name",
      "quantity": 1.5,
      "unit": "lbs",
      "category": "meat"
    }
  ]
}
IMPORTANT: All ingredient quantities must be scaled for exactly 1 standard serving.
The app handles all scaling for household size automatically.
All quantities must reflect the raw, pre-cooking weight or volume as it would be purchased at the grocery store.
Account for cooking loss — for example, meat quantities should be raw weight (chicken loses ~25% when cooked, ground beef ~20%), and vegetables should be unprepped weight.
Valid category values: produce, meat, dairy, pantry, frozen, bakery, other
Valid unit examples: lbs, oz, cups, tbsp, tsp, whole, cloves, slices, cans
Return exactly one recipe per slot requested. No additional text, only JSON."""


class ClaudeAdapter(AIPort):
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model

    async def suggest_recipes(self, request: SuggestionRequest) -> List[Recipe]:
        prompt = self._build_suggestion_prompt(request)
        return await self._call_and_parse(prompt, expected_count=len(request.slots))

    async def refine_recipes(self, request: RefinementRequest) -> List[Recipe]:
        prompt = self._build_refinement_prompt(request)
        return await self._call_and_parse(prompt, expected_count=len(request.slots))

    # ------------------------------------------------------------------
    # Prompt builders
    # ------------------------------------------------------------------

    @staticmethod
    def _build_suggestion_prompt(request: SuggestionRequest) -> str:
        slots_desc = "\n".join(
            f"- {s.name} ({s.meal_type.value}, {s.day_count} days)"
            for s in request.slots
        )
        member_names = [m.name for m in request.members]
        lines = [
            f"Suggest one recipe for each of these meal slots:\n{slots_desc}",
            "",
            "Household context:",
            f"- Members: {member_names}",
        ]
        if request.disliked_ingredients:
            lines.append(f"- Disliked ingredients: {request.disliked_ingredients}")
        if request.liked_ingredients:
            lines.append(f"- Liked ingredients: {request.liked_ingredients}")
        if request.cuisine_preferences:
            lines.append(f"- Preferred cuisines: {request.cuisine_preferences}")
        if request.week_context:
            lines.append(f"- This week: {request.week_context}")
        lines.append("")
        lines.append(f"Return a JSON array with exactly {len(request.slots)} recipes.")
        return "\n".join(lines)

    @staticmethod
    def _build_refinement_prompt(request: RefinementRequest) -> str:
        existing_desc = "\n".join(
            f"- {slot_id}: {recipe.name}"
            for slot_id, recipe in request.existing_assignments.items()
        )
        lines = [
            f'User request: "{request.user_message}"',
            "",
            "Current meal plan:",
            existing_desc,
            "",
        ]
        if request.slot_id_to_refine:
            lines.append(f"Only change the slot with id: {request.slot_id_to_refine}")
        else:
            lines.append("You may change any or all slots as needed.")

        slots_desc = "\n".join(
            f"- {s.name} ({s.meal_type.value}, {s.day_count} days)"
            for s in request.slots
        )
        lines += [
            "",
            f"All meal slots:\n{slots_desc}",
            "",
            f"Return a JSON array with exactly {len(request.slots)} recipes (one per slot, in order).",
        ]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # API call + parsing
    # ------------------------------------------------------------------

    async def _call_and_parse(self, prompt: str, expected_count: int) -> List[Recipe]:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()

        # Strip markdown code fences if the model wrapped the JSON
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        data = json.loads(raw)
        if not isinstance(data, list):
            raise ValueError(f"Expected JSON array from AI, got: {type(data)}")
        if len(data) != expected_count:
            raise ValueError(
                f"Expected {expected_count} recipes from AI, got {len(data)}"
            )

        return [self._parse_recipe(item) for item in data]

    @staticmethod
    def _parse_recipe(data: dict) -> Recipe:
        ingredients = [
            Ingredient(
                name=ing["name"],
                quantity=float(ing["quantity"]),
                unit=ing["unit"],
                category=GroceryCategory(ing["category"]),
            )
            for ing in data.get("ingredients", [])
        ]
        return Recipe(
            id=uuid4(),  # AI-suggested recipes get fresh IDs; persisted on confirm
            name=data["name"],
            emoji=data.get("emoji", "🍽️"),
            prep_time=int(data.get("prep_time", 30)),
            ingredients=ingredients,
            key_ingredients=list(data.get("key_ingredients", [])),
        )
