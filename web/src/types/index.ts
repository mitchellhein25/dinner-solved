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
