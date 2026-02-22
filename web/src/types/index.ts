export interface HouseholdMember {
  id: string
  name: string
  emoji: string
  serving_size: number
}

export interface Ingredient {
  name: string
  quantity: number
  unit: string
  category: string
}

export interface Recipe {
  id: string
  name: string
  emoji: string
  prep_time: number
  ingredients: Ingredient[]
  key_ingredients: string[]
  is_favorite: boolean
  source_url?: string | null
}

export interface MealSlot {
  id: string
  name: string
  meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack'
  days: string[]
  member_ids: string[]
}

export interface MealPlanTemplate {
  id: string
  slots: MealSlot[]
}

/** Used only when confirming — 1 chosen recipe per slot sent to the API. */
export interface RecipeSuggestion {
  slot: MealSlot
  recipe: Recipe
}

export interface SlotAssignment {
  slot_id: string
  recipe_id: string
}

export interface WeeklyPlan {
  id: string
  week_start_date: string
  assignments: SlotAssignment[]
}

export interface GroceryListItem {
  name: string
  quantity: number
  unit: string
  category: string
  recipe_names: string[]
}

export interface UserPreferences {
  id: string
  liked_ingredients: string[]
  disliked_ingredients: string[]
  cuisine_preferences: string[]
}

/** Per-slot state in the planning UI. */
export interface SlotState {
  slot: MealSlot
  options: Recipe[]          // 3 candidates from AI
  chosenIndex: number | null // index into options[], or null if not chosen
  locked: boolean
  regenerating: boolean      // true while a per-slot regenerate is in-flight
}

export interface GenerationBudget {
  remaining: number       // 0.0–3.0
  resetsAt: string | null // ISO timestamp, null if budget not yet started
}

/** Summary item returned by GET /api/recipes. */
export interface RecipeListItem {
  id: string
  name: string
  emoji: string
  prep_time: number
  key_ingredients: string[]
  is_favorite: boolean
  times_used: number
  last_used_at: string | null
}

/** Full detail returned by GET /api/recipes/:id. */
export interface RecipeDetail {
  id: string
  name: string
  emoji: string
  prep_time: number
  ingredients: Ingredient[]
  key_ingredients: string[]
  is_favorite: boolean
  cooking_instructions: string[] | null
  times_used: number
  last_used_at: string | null
  source_url: string | null
}

export const DAY_LABELS: Record<string, string> = {
  mon: 'Mon',
  tue: 'Tue',
  wed: 'Wed',
  thu: 'Thu',
  fri: 'Fri',
  sat: 'Sat',
  sun: 'Sun',
}

export const MEAL_TYPE_LABELS: Record<string, string> = {
  breakfast: 'Breakfast',
  lunch: 'Lunch',
  dinner: 'Dinner',
  snack: 'Snack',
}

export const CATEGORY_LABELS: Record<string, string> = {
  produce: 'Produce',
  meat: 'Meat',
  dairy: 'Dairy',
  pantry: 'Pantry',
  frozen: 'Frozen',
  bakery: 'Bakery',
  other: 'Other',
}
