import json
from typing import List
from uuid import uuid4

import httpx
from anthropic import AsyncAnthropic

from application.ports.ai_port import AIPort, RefinementRequest, SuggestionRequest
from domain.entities.recipe import GroceryCategory, Ingredient, Recipe

# The model ID must match an available Claude model.
DEFAULT_MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a meal planning assistant for Dinner Solved.
When asked to suggest recipes, respond ONLY with a valid JSON array of arrays.
Each inner array contains exactly 3 distinct recipe options for one slot.
Structure: [[option1, option2, option3], [option1, option2, option3], ...]

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
The 3 options per slot must be meaningfully different from each other.
No additional text outside the JSON array."""


class ClaudeAdapter(AIPort):
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model

    async def suggest_recipes(self, request: SuggestionRequest) -> List[List[Recipe]]:
        prompt = self._build_suggestion_prompt(request)
        return await self._call_and_parse(prompt, expected_slot_count=len(request.slots))

    async def generate_instructions(self, recipe: Recipe) -> List[str]:
        ingredients_text = "\n".join(
            f"- {ing.quantity} {ing.unit} {ing.name}" for ing in recipe.ingredients
        )
        prompt = (
            f"Recipe: {recipe.name}\n"
            f"Prep time: {recipe.prep_time} minutes\n"
            f"Ingredients (per serving):\n{ingredients_text}\n\n"
            "Return step-by-step cooking instructions as a JSON array of strings. "
            "Each string is one step (1-3 sentences). Aim for 6-10 steps total."
        )
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=(
                "You are a cooking assistant. Return cooking instructions as a JSON array of step strings. "
                "Respond ONLY with the JSON array. No additional text."
            ),
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        steps = json.loads(raw)
        if not isinstance(steps, list):
            raise ValueError("Expected JSON array from generate_instructions")
        return [str(s) for s in steps]

    async def refine_recipes(self, request: RefinementRequest) -> List[List[Recipe]]:
        unlocked_slots = [
            s for s in request.slots if str(s.id) not in request.locked_slot_ids
        ]
        if not unlocked_slots:
            return []
        prompt = self._build_refinement_prompt(request, unlocked_slots)
        return await self._call_and_parse(prompt, expected_slot_count=len(unlocked_slots))

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
            f"Suggest 3 different recipe options for each of these meal slots:\n{slots_desc}",
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
        if request.recent_recipe_names:
            names = ", ".join(request.recent_recipe_names)
            lines.append(f"- Used in the last 2 weeks (aim for variety): {names}")
        lines.append("")
        lines.append(
            f"Return a JSON array of arrays with exactly {len(request.slots)} inner arrays, "
            f"each containing exactly 3 recipe objects."
        )
        return "\n".join(lines)

    @staticmethod
    def _build_refinement_prompt(
        request: RefinementRequest, unlocked_slots: list
    ) -> str:
        existing_desc = "\n".join(
            f"- {slot_id}: {recipe.name}"
            for slot_id, recipe in request.existing_assignments.items()
        )
        locked_ids = set(request.locked_slot_ids)
        locked_desc = "\n".join(
            f"- {s.name} (LOCKED — do not change)"
            for s in request.slots
            if str(s.id) in locked_ids
        )
        unlocked_desc = "\n".join(
            f"- {s.name} ({s.meal_type.value}, {s.day_count} days)"
            for s in unlocked_slots
        )
        lines = [
            f'User request: "{request.user_message}"',
            "",
            "Current meal plan:",
            existing_desc,
        ]
        if locked_desc:
            lines += ["", "Locked slots (keep as-is):", locked_desc]
        lines += [
            "",
            f"Provide 3 options for each of these {len(unlocked_slots)} unlocked slot(s):",
            unlocked_desc,
            "",
            f"Return a JSON array of arrays with exactly {len(unlocked_slots)} inner arrays, "
            f"each containing exactly 3 recipe objects.",
        ]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # API call + parsing
    # ------------------------------------------------------------------

    async def _call_and_parse(
        self, prompt: str, expected_slot_count: int
    ) -> List[List[Recipe]]:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=8192,
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
        if len(data) != expected_slot_count:
            raise ValueError(
                f"Expected {expected_slot_count} slot groups from AI, got {len(data)}"
            )

        result: List[List[Recipe]] = []
        for i, inner in enumerate(data):
            if not isinstance(inner, list) or len(inner) != 3:
                count = len(inner) if isinstance(inner, list) else "non-list"
                raise ValueError(
                    f"Slot {i}: expected 3 recipe options, got {count}"
                )
            result.append([self._parse_recipe(item) for item in inner])

        return result

    async def parse_recipe_from_url(self, url: str) -> Recipe:
        """Fetch a webpage via tool use and extract a recipe from it."""
        fetch_tool = {
            "name": "fetch_webpage",
            "description": "Fetch the HTML content of a webpage to extract recipe information.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to fetch"},
                },
                "required": ["url"],
            },
        }
        system = (
            "You are a recipe parser for Dinner Solved. Use the fetch_webpage tool to retrieve "
            "the page, then extract the recipe and return it as a single JSON object.\n\n"
            "The JSON must follow this exact structure:\n"
            "{\n"
            '  "name": "Recipe Name",\n'
            '  "emoji": "🍝",\n'
            '  "prep_time": 30,\n'
            '  "key_ingredients": ["ingredient1", "ingredient2", "ingredient3"],\n'
            '  "ingredients": [\n'
            '    {"name": "ingredient name", "quantity": 1.5, "unit": "lbs", "category": "meat"}\n'
            "  ],\n"
            '  "cooking_instructions": ["Step 1...", "Step 2..."]\n'
            "}\n\n"
            "IMPORTANT: All ingredient quantities must be for exactly 1 standard serving.\n"
            "Valid category values: produce, meat, dairy, pantry, frozen, bakery, other\n"
            'If the page contains no recipe, return {"error": "No recipe found"}.\n'
            "Respond ONLY with the JSON object. No additional text."
        )
        messages: list = [{"role": "user", "content": f"Extract the recipe from this URL: {url}"}]

        # Agentic loop — let Claude call the tool until it produces a final response
        for _ in range(5):  # max 5 turns (in practice 2: fetch + parse)
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=4096,
                system=system,
                tools=[fetch_tool],
                messages=messages,
            )

            if response.stop_reason == "tool_use":
                # Collect all tool calls in this turn
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use" and block.name == "fetch_webpage":
                        fetch_url = block.input.get("url", url)
                        try:
                            async with httpx.AsyncClient(
                                follow_redirects=True, timeout=15.0
                            ) as client:
                                r = await client.get(
                                    fetch_url,
                                    headers={"User-Agent": "Mozilla/5.0 (compatible; DinnerSolvedBot/1.0)"},
                                )
                                content = r.text[:40000]  # cap to ~10k tokens
                        except Exception as exc:
                            content = f"Error fetching URL: {exc}"
                        tool_results.append(
                            {"type": "tool_result", "tool_use_id": block.id, "content": content}
                        )

                # Append assistant turn + tool results and continue
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
                continue

            # stop_reason == "end_turn" — parse the JSON response
            raw = next(
                (b.text for b in response.content if hasattr(b, "text")), ""
            ).strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()
            data = json.loads(raw)
            if "error" in data:
                raise ValueError(data["error"])
            return self._parse_recipe_with_instructions(data)

        raise ValueError("Failed to extract recipe after multiple attempts")

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

    @staticmethod
    def _parse_recipe_with_instructions(data: dict) -> Recipe:
        """Like _parse_recipe but also captures cooking_instructions if present."""
        ingredients = [
            Ingredient(
                name=ing["name"],
                quantity=float(ing["quantity"]),
                unit=ing["unit"],
                category=GroceryCategory(ing["category"]),
            )
            for ing in data.get("ingredients", [])
        ]
        instructions = data.get("cooking_instructions")
        if isinstance(instructions, list):
            instructions = [str(s) for s in instructions] or None
        else:
            instructions = None
        return Recipe(
            id=uuid4(),
            name=data["name"],
            emoji=data.get("emoji", "🍽️"),
            prep_time=int(data.get("prep_time", 30)),
            ingredients=ingredients,
            key_ingredients=list(data.get("key_ingredients", [])),
            cooking_instructions=instructions,
        )
