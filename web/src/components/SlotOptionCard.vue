<script setup lang="ts">
import type { Recipe } from '@/types'

defineProps<{
  recipe: Recipe
  selected: boolean
  disabled: boolean
}>()

const emit = defineEmits<{
  select: []
}>()
</script>

<template>
  <button
    class="slot-option-card"
    :class="{ 'slot-option-card--selected': selected, 'slot-option-card--disabled': disabled }"
    :disabled="disabled"
    @click="!disabled && emit('select')"
  >
    <div class="slot-option-card__emoji">{{ recipe.emoji }}</div>
    <div class="slot-option-card__name">{{ recipe.name }}</div>
    <div class="slot-option-card__ingredients">
      {{ recipe.key_ingredients.slice(0, 3).join(' · ') }}
    </div>
    <div class="slot-option-card__meta">{{ recipe.prep_time }} min</div>
  </button>
</template>

<style scoped>
.slot-option-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  padding: 0.75rem 0.5rem;
  background: var(--card-bg);
  border: 2px solid var(--border);
  border-radius: var(--radius);
  cursor: pointer;
  text-align: center;
  transition: border-color 0.15s, box-shadow 0.15s, opacity 0.15s;
  width: 100%;
  min-height: 7rem;
}

.slot-option-card:hover:not(.slot-option-card--disabled) {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--accent) 20%, transparent);
}

.slot-option-card--selected {
  border-color: var(--accent);
  background: color-mix(in srgb, var(--accent) 8%, var(--card-bg));
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--accent) 25%, transparent);
}

.slot-option-card--disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.slot-option-card__emoji {
  font-size: 1.75rem;
  line-height: 1;
}

.slot-option-card__name {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--ink);
  line-height: 1.2;
  /* Clamp to 2 lines so long names don't explode the card height */
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  width: 100%;
}

.slot-option-card__ingredients {
  font-size: 0.6875rem;
  color: var(--ink-light);
  line-height: 1.3;
  /* Clamp ingredients to 1 line */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%;
}

.slot-option-card__meta {
  font-size: 0.6875rem;
  color: var(--ink-light);
}
</style>
