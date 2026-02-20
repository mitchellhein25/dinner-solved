# Dinner Solved
## Claude Code Project Brief — v1

---

## Project Overview

**Dinner Solved** is a web-based AI-powered meal planning app that eliminates the weekly mental load of figuring out what to cook and what to buy. The user sets up their household and meal template once, then each week the app suggests recipes, lets them refine via chat, and generates a scaled, merged grocery list ready to export.

**Target audience:** Parents (primarily moms, but not exclusively) planning weekly meals for their family.

**Core value proposition:** Open the app → get recipe suggestions → confirm → grocery list done. Minimal friction, maximum automation.

---

## Architecture Overview

Dinner Solved follows **Clean Architecture** principles. The Python API is the system's brain — it owns all business logic and could theoretically power any frontend, mobile app, CLI, or third-party integration without modification.

```
┌─────────────────────────────────────────────────────────┐
│                        Clients                          │
│         Vue.js Web App   │   (Future: Mobile, CLI)      │
└─────────────────┬───────────────────────────────────────┘
                  │  HTTP / REST
┌─────────────────▼───────────────────────────────────────┐
│                   FastAPI (Python)                       │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              API Layer (Routers)                 │   │
│  │   /household  /template  /plan  /grocery  /prefs │   │
│  └────────────────────┬────────────────────────────┘   │
│                        │                                │
│  ┌─────────────────────▼────────────────────────────┐  │
│  │             Application Layer (Use Cases)         │  │
│  │  SuggestRecipes  │  RefinePlan  │  BuildGrocery   │  │
│  └─────────────────────┬────────────────────────────┘  │
│                         │                               │
│  ┌──────────────────────▼───────────────────────────┐  │
│  │              Domain Layer (Core)                  │  │
│  │   Entities  │  Business Rules  │  Domain Services │  │
│  └──────────────────────┬───────────────────────────┘  │
│                          │                              │
│  ┌───────────────────────▼──────────────────────────┐  │
│  │         Infrastructure Layer (Adapters)           │  │
│  │   PostgreSQL  │  Claude API  │  Sheets  │  CSV    │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Key Architectural Principles

1. **The API stands alone** — the Python backend has no knowledge of Vue, the browser, or any specific client. It speaks JSON over HTTP only.
2. **Dependency inversion everywhere** — business logic depends on abstractions (interfaces), not concrete implementations. Swap PostgreSQL for MongoDB, or Claude for GPT-4, without touching domain code.
3. **Database is plug and play** — the domain layer never imports SQLAlchemy, psycopg2, or any DB driver. All persistence goes through repository interfaces.
4. **UI is a thin client** — Vue.js only handles presentation and user interaction. It contains zero business logic.
5. **AI provider is an adapter** — the Claude API is treated as an infrastructure concern, not a core dependency.

---

## Project Structure

```
dinner-solved/
│
├── api/                          # Python FastAPI backend
│   ├── src/
│   │   ├── domain/               # Enterprise business rules — pure Python, no frameworks
│   │   │   ├── entities/         # Core data models (dataclasses, no ORM)
│   │   │   │   ├── household.py
│   │   │   │   ├── recipe.py
│   │   │   │   ├── meal_plan.py
│   │   │   │   └── grocery.py
│   │   │   ├── repositories/     # Abstract interfaces (ABC) — no implementations
│   │   │   │   ├── household_repository.py
│   │   │   │   ├── recipe_repository.py
│   │   │   │   ├── meal_plan_repository.py
│   │   │   │   └── preference_repository.py
│   │   │   ├── services/         # Domain services — pure business logic
│   │   │   │   ├── grocery_list_service.py
│   │   │   │   ├── meal_plan_service.py
│   │   │   │   └── serving_calculator.py
│   │   │   └── value_objects/    # Immutable domain concepts
│   │   │       ├── serving_size.py
│   │   │       ├── ingredient.py
│   │   │       └── day_of_week.py
│   │   │
│   │   ├── application/          # Application use cases — orchestrates domain
│   │   │   ├── use_cases/
│   │   │   │   ├── suggest_recipes.py
│   │   │   │   ├── refine_recipes.py
│   │   │   │   ├── build_grocery_list.py
│   │   │   │   ├── manage_household.py
│   │   │   │   └── manage_template.py
│   │   │   └── ports/            # Interfaces for external services
│   │   │       ├── ai_port.py
│   │   │       └── export_port.py
│   │   │
│   │   ├── infrastructure/       # Concrete implementations — swappable
│   │   │   ├── db/
│   │   │   │   ├── postgres/
│   │   │   │   │   ├── models.py           # SQLAlchemy ORM models
│   │   │   │   │   ├── household_repo.py   # Implements domain interface
│   │   │   │   │   ├── recipe_repo.py
│   │   │   │   │   ├── meal_plan_repo.py
│   │   │   │   │   └── preference_repo.py
│   │   │   │   └── migrations/             # Alembic migrations
│   │   │   ├── ai/
│   │   │   │   └── claude_adapter.py       # Implements ai_port.py
│   │   │   └── export/
│   │   │       ├── csv_adapter.py          # Implements export_port.py
│   │   │       └── google_sheets_adapter.py
│   │   │
│   │   └── api/                  # FastAPI layer — HTTP only, no business logic
│   │       ├── routers/
│   │       │   ├── household.py
│   │       │   ├── template.py
│   │       │   ├── plan.py
│   │       │   ├── grocery.py
│   │       │   └── preferences.py
│   │       ├── schemas/          # Pydantic request/response models
│   │       │   ├── household.py
│   │       │   ├── recipe.py
│   │       │   ├── plan.py
│   │       │   └── grocery.py
│   │       ├── dependencies.py   # DI container — wires interfaces to implementations
│   │       └── main.py
│   │
│   ├── tests/
│   │   ├── unit/                 # Test domain services in isolation (no DB, no API)
│   │   ├── integration/          # Test repositories against real DB
│   │   └── e2e/                  # Test full API flows
│   ├── pyproject.toml
│   ├── .env.example
│   └── Dockerfile
│
├── web/                          # Vue 3 frontend — thin client only
│   ├── src/
│   │   ├── api/                  # API client layer (all HTTP calls live here)
│   │   │   ├── client.ts         # Axios/fetch base config
│   │   │   ├── household.ts
│   │   │   ├── plan.ts
│   │   │   └── grocery.ts
│   │   ├── stores/               # Pinia — UI state only, no business logic
│   │   │   ├── household.ts
│   │   │   ├── plan.ts
│   │   │   └── onboarding.ts
│   │   ├── views/
│   │   │   ├── onboarding/
│   │   │   │   ├── Welcome.vue
│   │   │   │   ├── HouseholdSetup.vue
│   │   │   │   ├── ServingSizes.vue
│   │   │   │   └── MealTemplate.vue
│   │   │   ├── planner/
│   │   │   │   ├── WeeklyOverview.vue
│   │   │   │   ├── RecipeSuggestions.vue
│   │   │   │   └── GroceryList.vue
│   │   │   └── settings/
│   │   │       └── Settings.vue
│   │   ├── components/           # Reusable UI components
│   │   ├── router/
│   │   └── types/                # TypeScript types mirroring API schemas
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── docker-compose.yml            # Local dev: API + DB + web
└── README.md
```

---

## Domain Entities (Python)

```python
# api/src/domain/entities/household.py
from dataclasses import dataclass, field
from uuid import UUID

@dataclass
class HouseholdMember:
    id: UUID
    name: str
    emoji: str
    serving_size: float  # e.g. 1.5, 1.0, 0.25 — multiplier against 1 standard serving


# api/src/domain/entities/meal_plan.py
from dataclasses import dataclass
from enum import Enum
from typing import List
from uuid import UUID

class MealType(Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"

class DayOfWeek(Enum):
    MON = "mon"
    TUE = "tue"
    WED = "wed"
    THU = "thu"
    FRI = "fri"
    SAT = "sat"
    SUN = "sun"

@dataclass
class MealSlot:
    id: UUID
    name: str                        # e.g. "Weekday Lunches", "Dinner A"
    meal_type: MealType
    days: List[DayOfWeek]            # which days this slot covers
    member_ids: List[UUID]           # which household members eat this meal

    @property
    def day_count(self) -> int:
        return len(self.days)

@dataclass
class MealPlanTemplate:
    id: UUID
    slots: List[MealSlot]

@dataclass
class SlotAssignment:
    slot_id: UUID
    recipe_id: UUID

@dataclass
class WeeklyPlan:
    id: UUID
    week_start_date: str             # ISO date string e.g. "2026-02-23"
    assignments: List[SlotAssignment]


# api/src/domain/entities/recipe.py
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from uuid import UUID

class GroceryCategory(Enum):
    PRODUCE = "produce"
    MEAT = "meat"
    DAIRY = "dairy"
    PANTRY = "pantry"
    FROZEN = "frozen"
    BAKERY = "bakery"
    OTHER = "other"

@dataclass
class Ingredient:
    name: str
    quantity: float
    unit: str                        # 'lbs', 'oz', 'cups', 'tbsp', 'tsp', 'whole', etc.
    category: GroceryCategory
    # IMPORTANT: quantity is always for 1 standard serving
    # GroceryListService handles all scaling

@dataclass
class Recipe:
    id: UUID
    name: str
    emoji: str
    prep_time: int                   # minutes
    ingredients: List[Ingredient]
    key_ingredients: List[str]       # short summary for display e.g. ['chicken', 'rice']
    is_favorite: bool = False
    source_url: Optional[str] = None


# api/src/domain/entities/grocery.py
from dataclasses import dataclass, field
from typing import List
from .recipe import GroceryCategory

@dataclass
class GroceryListItem:
    name: str
    quantity: float
    unit: str
    category: GroceryCategory
    recipe_names: List[str]          # which recipes contributed this item
```

---

## Repository Interfaces (Abstract — Domain Layer)

```python
# api/src/domain/repositories/household_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from ..entities.household import HouseholdMember

class HouseholdRepository(ABC):
    @abstractmethod
    async def get_members(self) -> List[HouseholdMember]: ...

    @abstractmethod
    async def save_members(self, members: List[HouseholdMember]) -> None: ...

    @abstractmethod
    async def get_member(self, member_id: UUID) -> Optional[HouseholdMember]: ...


# api/src/domain/repositories/meal_plan_repository.py
from abc import ABC, abstractmethod
from typing import Optional
from ..entities.meal_plan import MealPlanTemplate, WeeklyPlan

class MealPlanTemplateRepository(ABC):
    @abstractmethod
    async def get_template(self) -> Optional[MealPlanTemplate]: ...

    @abstractmethod
    async def save_template(self, template: MealPlanTemplate) -> None: ...

class WeeklyPlanRepository(ABC):
    @abstractmethod
    async def get_plan(self, week_start_date: str) -> Optional[WeeklyPlan]: ...

    @abstractmethod
    async def save_plan(self, plan: WeeklyPlan) -> None: ...


# api/src/domain/repositories/recipe_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from ..entities.recipe import Recipe

class RecipeRepository(ABC):
    @abstractmethod
    async def save_recipe(self, recipe: Recipe) -> None: ...

    @abstractmethod
    async def get_recipes(self) -> List[Recipe]: ...

    @abstractmethod
    async def get_recipe(self, recipe_id: UUID) -> Optional[Recipe]: ...

    @abstractmethod
    async def get_favorites(self) -> List[Recipe]: ...

    @abstractmethod
    async def toggle_favorite(self, recipe_id: UUID) -> None: ...
```

---

## Application Ports (External Service Interfaces)

```python
# api/src/application/ports/ai_port.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from ...domain.entities.recipe import Recipe
from ...domain.entities.meal_plan import MealSlot
from ...domain.entities.household import HouseholdMember

@dataclass
class SuggestionRequest:
    slots: List[MealSlot]
    members: List[HouseholdMember]
    disliked_ingredients: List[str]
    liked_ingredients: List[str]
    cuisine_preferences: List[str]
    week_context: Optional[str] = None   # e.g. "feeling like something light"

@dataclass
class RefinementRequest(SuggestionRequest):
    existing_assignments: dict           # slot_id -> Recipe
    user_message: str                    # e.g. "swap the pasta for something lighter"
    slot_id_to_refine: Optional[str] = None

class AIPort(ABC):
    @abstractmethod
    async def suggest_recipes(self, request: SuggestionRequest) -> List[Recipe]: ...

    @abstractmethod
    async def refine_recipes(self, request: RefinementRequest) -> List[Recipe]: ...


# api/src/application/ports/export_port.py
from abc import ABC, abstractmethod
from typing import List
from ...domain.entities.grocery import GroceryListItem

class ExportPort(ABC):
    @abstractmethod
    async def export(self, items: List[GroceryListItem], week_start_date: str) -> str:
        # returns a URL, file path, or confirmation string depending on adapter
        ...
```

---

## Key Domain Services

### GroceryListService
The most critical service in the system.

```python
# api/src/domain/services/grocery_list_service.py
from typing import List, Dict
from ..entities.grocery import GroceryListItem
from ..entities.recipe import Recipe, Ingredient, GroceryCategory
from ..entities.meal_plan import MealSlot, WeeklyPlan
from ..entities.household import HouseholdMember
from .serving_calculator import ServingCalculator

class GroceryListService:
    def __init__(self, serving_calculator: ServingCalculator):
        self._calc = serving_calculator

    def build(
        self,
        weekly_plan: WeeklyPlan,
        slots: List[MealSlot],
        members: List[HouseholdMember],
        recipes: Dict[str, Recipe]       # recipe_id -> Recipe
    ) -> List[GroceryListItem]:
        """
        For each slot assignment:
          1. Calculate total servings = sum(member.serving_size) * slot.day_count
          2. Scale each ingredient by total servings
          3. Merge duplicate ingredients across all recipes
          4. Return sorted by category
        """
        raw_items: List[GroceryListItem] = []

        for assignment in weekly_plan.assignments:
            slot = next(s for s in slots if s.id == assignment.slot_id)
            recipe = recipes[str(assignment.recipe_id)]
            total_servings = self._calc.total_servings(slot, members)

            for ingredient in recipe.ingredients:
                raw_items.append(GroceryListItem(
                    name=ingredient.name,
                    quantity=round(ingredient.quantity * total_servings, 2),
                    unit=ingredient.unit,
                    category=ingredient.category,
                    recipe_names=[recipe.name]
                ))

        return self._merge_and_sort(raw_items)

    def _merge_and_sort(self, items: List[GroceryListItem]) -> List[GroceryListItem]:
        # Merge items with matching name + unit
        # Sort by category then name
        ...


# api/src/domain/services/serving_calculator.py
class ServingCalculator:
    def total_servings(self, slot: MealSlot, members: List[HouseholdMember]) -> float:
        """
        Sum serving sizes of members assigned to this slot,
        multiplied by the number of days the slot covers.
        e.g. Mitch(1.5) + Wife(1.0) + Daughter(0.25) = 2.75 * 3 days = 8.25
        """
        slot_members = [m for m in members if m.id in slot.member_ids]
        per_meal = sum(m.serving_size for m in slot_members)
        return round(per_meal * slot.day_count, 2)
```

---

## Claude API Adapter

```python
# api/src/infrastructure/ai/claude_adapter.py
import json
from anthropic import AsyncAnthropic
from ...application.ports.ai_port import AIPort, SuggestionRequest, RefinementRequest
from ...domain.entities.recipe import Recipe

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
Valid category values: produce, meat, dairy, pantry, frozen, bakery, other
Return exactly one recipe per slot requested. No additional text, only JSON."""

class ClaudeAdapter(AIPort):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model

    async def suggest_recipes(self, request: SuggestionRequest) -> List[Recipe]:
        prompt = self._build_suggestion_prompt(request)
        return await self._call_and_parse(prompt)

    async def refine_recipes(self, request: RefinementRequest) -> List[Recipe]:
        prompt = self._build_refinement_prompt(request)
        return await self._call_and_parse(prompt)

    def _build_suggestion_prompt(self, request: SuggestionRequest) -> str:
        slots_desc = "\n".join([
            f"- {s.name} ({s.meal_type.value}, {s.day_count} days)"
            for s in request.slots
        ])
        return f"""Suggest one recipe for each of these meal slots:
{slots_desc}

Household context:
- Members: {[m.name for m in request.members]}
- Disliked ingredients: {request.disliked_ingredients}
- Preferred cuisines: {request.cuisine_preferences}
{f'- This week: {request.week_context}' if request.week_context else ''}

Return a JSON array with exactly {len(request.slots)} recipes."""

    async def _call_and_parse(self, prompt: str) -> List[Recipe]:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        data = json.loads(raw)
        return [self._parse_recipe(r) for r in data]

    def _parse_recipe(self, data: dict) -> Recipe:
        # parse and validate JSON into Recipe entity
        ...
```

---

## FastAPI Layer

```python
# api/src/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import household, template, plan, grocery, preferences

app = FastAPI(title="Dinner Solved API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vue dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(household.router, prefix="/api/household", tags=["household"])
app.include_router(template.router, prefix="/api/template", tags=["template"])
app.include_router(plan.router, prefix="/api/plan", tags=["plan"])
app.include_router(grocery.router, prefix="/api/grocery", tags=["grocery"])
app.include_router(preferences.router, prefix="/api/preferences", tags=["preferences"])


# api/src/api/dependencies.py
# Dependency injection — wire interfaces to concrete implementations here
# Swap implementations by changing this file only

from functools import lru_cache
from ..infrastructure.db.postgres.household_repo import PostgresHouseholdRepository
from ..infrastructure.ai.claude_adapter import ClaudeAdapter
from ..domain.services.grocery_list_service import GroceryListService
from ..domain.services.serving_calculator import ServingCalculator
from ..application.use_cases.suggest_recipes import SuggestRecipesUseCase
import os

@lru_cache
def get_household_repo():
    return PostgresHouseholdRepository(connection_string=os.getenv("DATABASE_URL"))

@lru_cache
def get_ai_adapter():
    return ClaudeAdapter(api_key=os.getenv("ANTHROPIC_API_KEY"))

@lru_cache
def get_grocery_service():
    return GroceryListService(serving_calculator=ServingCalculator())

@lru_cache
def get_suggest_use_case():
    return SuggestRecipesUseCase(
        ai_adapter=get_ai_adapter(),
        template_repo=get_template_repo(),
        household_repo=get_household_repo(),
        preference_repo=get_preference_repo()
    )
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/household/members` | Get all household members |
| POST | `/api/household/members` | Save household members |
| GET | `/api/template` | Get meal plan template |
| POST | `/api/template` | Save meal plan template |
| GET | `/api/plan/{week_start_date}` | Get weekly plan |
| POST | `/api/plan/suggest` | Get AI recipe suggestions |
| POST | `/api/plan/refine` | Refine suggestions via chat |
| POST | `/api/plan/confirm` | Confirm weekly plan |
| GET | `/api/grocery/{week_start_date}` | Get grocery list |
| POST | `/api/grocery/export/csv` | Export as CSV |
| POST | `/api/grocery/export/sheets` | Export to Google Sheets |
| GET | `/api/preferences` | Get user preferences |
| POST | `/api/preferences` | Save user preferences |

---

## Database — PostgreSQL (Initial Implementation)

Tables (initial schema):

```sql
-- Household
household_members (id, name, emoji, serving_size, created_at)

-- Template
meal_plan_templates (id, created_at, updated_at)
meal_slots (id, template_id, name, meal_type, days[], created_at)
meal_slot_members (slot_id, member_id)

-- Plans
weekly_plans (id, week_start_date, created_at)
slot_assignments (id, plan_id, slot_id, recipe_id)

-- Recipes
recipes (id, name, emoji, prep_time, key_ingredients[], is_favorite, source_url, created_at)
ingredients (id, recipe_id, name, quantity, unit, category)

-- Preferences
user_preferences (id, liked_ingredients[], disliked_ingredients jsonb, cuisine_preferences[])
```

Use **Alembic** for migrations.

---

## Vue.js Frontend (Thin Client)

The Vue app has one job: present data and collect user input. All logic lives in the API.

```typescript
// web/src/api/plan.ts — example API client
import { apiClient } from './client'

export const planApi = {
  suggest: (weekContext?: string) =>
    apiClient.post('/api/plan/suggest', { week_context: weekContext }),

  refine: (userMessage: string, slotIdToRefine?: string) =>
    apiClient.post('/api/plan/refine', { user_message: userMessage, slot_id_to_refine: slotIdToRefine }),

  confirm: (assignments: SlotAssignment[]) =>
    apiClient.post('/api/plan/confirm', { assignments }),

  getGroceryList: (weekStartDate: string) =>
    apiClient.get(`/api/grocery/${weekStartDate}`),

  exportCsv: (weekStartDate: string) =>
    apiClient.post('/api/grocery/export/csv', { week_start_date: weekStartDate }),
}
```

**Pinia stores** manage UI state only — loading states, current screen, form data. They call the API layer and store responses. No business logic.

---

## Design System

```css
:root {
  --cream: #F7F4EF;
  --warm-white: #FDFCFA;
  --ink: #1C1917;
  --ink-light: #6B6560;
  --accent: #C4693A;
  --accent-light: #F0E0D6;
  --green: #4A7C59;
  --green-light: #E4EDE7;
  --border: #E5E0D8;
  --card-bg: #FFFFFF;
}
```

**Fonts (Google Fonts):**
- Display/headings: `Fraunces` — serif, light weight, italic accents
- Body/UI: `DM Sans`

---

## UI Flow Summary

### Onboarding (first run only)
1. **Welcome** — What Dinner Solved does and why the setup matters
2. **Household Setup** — Add members with name and emoji
3. **Serving Sizes** — Set serving multiplier per member (0.25 increments). Explain what 1.0 means.
4. **Meal Template** — Define slots: name, meal type, days, which members eat it. Show computed total servings per slot.
→ Complete → redirect to weekly planner, never show again

### Weekly Planner (every week)
1. **Your Week** (`/`) — Template loaded, serving totals shown quietly per slot. CTA: "Suggest Recipes"
2. **Recipe Suggestions** (`/suggestions`) — One pre-selected recipe card per slot. Chat input for swaps.
3. **Grocery List** (`/grocery`) — Items by category, scaled for household. Export buttons.

### Settings (`/settings`)
- Edit household members + serving sizes
- Edit meal template
- Manage food preferences

---

## Key UX Rules

1. Serving totals shown quietly on each slot — e.g. "2.75 servings × 3 nights"
2. Recipe cards are pre-selected by default — user deselects, not selects
3. Chat is an escape hatch, not the primary interaction
4. Onboarding explains *why* each setting exists
5. Settings never appear in the main weekly flow
6. Export is the final step — CSV first, Google Sheets second

---

## Environment Variables

```bash
# api/.env
DATABASE_URL=postgresql://user:password@localhost:5432/dinner_solved
ANTHROPIC_API_KEY=your_key_here
ENVIRONMENT=development

# web/.env
VITE_API_BASE_URL=http://localhost:8000
```

> ⚠️ The Anthropic API key lives server-side only. The Vue app never touches it directly — all AI calls go through the FastAPI backend.

---

## Local Dev Setup

```yaml
# docker-compose.yml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: dinner_solved
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"

  api:
    build: ./api
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://user:password@db:5432/dinner_solved
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
    depends_on:
      - db

  web:
    build: ./web
    ports:
      - "5173:5173"
    environment:
      VITE_API_BASE_URL: http://localhost:8000
    depends_on:
      - api
```

---

## v1 Build Order (for Claude Code)

Build in this sequence — each step is independently testable:

1. **Scaffold monorepo** — `/api` and `/web` directories, docker-compose, README
2. **Domain entities** — pure Python dataclasses, no dependencies
3. **Repository interfaces** — abstract base classes
4. **Domain services** — `ServingCalculator`, `GroceryListService` with unit tests
5. **Application use cases** — `SuggestRecipes`, `RefineRecipes`, `BuildGroceryList`
6. **PostgreSQL repositories** — SQLAlchemy implementations of interfaces
7. **Alembic migrations** — initial schema
8. **Claude adapter** — implement `AIPort` using Anthropic SDK
9. **CSV export adapter** — implement `ExportPort`
10. **FastAPI routers + schemas** — wire everything via dependency injection
11. **Vue scaffold** — Vite + Vue 3 + TypeScript + Pinia + Vue Router
12. **API client layer** — all HTTP calls centralized
13. **Onboarding screens** — 4 screens, calls household + template endpoints
14. **Weekly planner screens** — 3 screens, calls plan + grocery endpoints
15. **Settings screen**
16. **Google Sheets export adapter** — after CSV is working

---

## Out of Scope for v1

- User authentication (single household, no login)
- Multiple meal plan templates
- Recipe clipping from URLs
- HEB or other grocery app integrations
- Mobile app
- Social or sharing features
- Nutritional tracking
- Pantry/inventory management
