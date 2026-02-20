<script setup lang="ts">
import type { MealSlot, Recipe } from '@/types'
import { DAY_LABELS, MEAL_TYPE_LABELS } from '@/types'

defineProps<{
  slot: MealSlot
  recipe: Recipe
  totalServings: number
}>()
</script>

<template>
  <div class="recipe-card">
    <div class="recipe-card__slot-label">
      <span class="chip">{{ MEAL_TYPE_LABELS[slot.meal_type] }}</span>
      <span class="recipe-card__days">
        {{ slot.days.map((d) => DAY_LABELS[d]).join(', ') }}
      </span>
      <span class="recipe-card__servings">{{ totalServings }} servings</span>
    </div>

    <div class="recipe-card__body">
      <div class="recipe-card__emoji">{{ recipe.emoji }}</div>
      <div class="recipe-card__info">
        <h3 class="recipe-card__name">{{ recipe.name }}</h3>
        <p class="recipe-card__key-ingredients">
          {{ recipe.key_ingredients.join(' · ') }}
        </p>
        <p class="recipe-card__meta">{{ recipe.prep_time }} min prep · {{ slot.name }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.recipe-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  overflow: hidden;
}
.recipe-card__slot-label {
  background: var(--cream);
  border-bottom: 1px solid var(--border);
  padding: 0.5rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.625rem;
}
.recipe-card__days {
  font-size: 0.8125rem;
  color: var(--ink-light);
}
.recipe-card__servings {
  font-size: 0.75rem;
  color: var(--ink-light);
  margin-left: auto;
}
.recipe-card__body {
  padding: 1rem;
  display: flex;
  gap: 0.875rem;
  align-items: flex-start;
}
.recipe-card__emoji {
  font-size: 2.25rem;
  line-height: 1;
  flex-shrink: 0;
}
.recipe-card__name {
  font-family: var(--font-display);
  font-size: 1.125rem;
  margin-bottom: 0.25rem;
}
.recipe-card__key-ingredients {
  font-size: 0.875rem;
  color: var(--ink-light);
  margin-bottom: 0.375rem;
}
.recipe-card__meta {
  font-size: 0.75rem;
  color: var(--ink-light);
}
</style>
