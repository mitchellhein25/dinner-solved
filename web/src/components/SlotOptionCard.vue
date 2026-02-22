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
  align-items: flex-start;
  gap: 0.2rem;
  padding: 0.875rem 0.75rem 0.75rem;
  background: var(--card-bg);
  border: 1.5px solid var(--border);
  border-radius: var(--radius);
  cursor: pointer;
  text-align: left;
  transition: border-color 0.15s, box-shadow 0.15s, background 0.15s;
  width: 100%;
  min-height: 7.5rem;
}

.slot-option-card:hover:not(.slot-option-card--disabled) {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 15%, transparent);
}

.slot-option-card--selected {
  border-color: var(--accent);
  background: var(--accent-light);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 20%, transparent);
}

.slot-option-card--disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.slot-option-card__emoji {
  font-size: 2rem;
  line-height: 1;
  margin-bottom: 0.3rem;
}

.slot-option-card__name {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--ink);
  line-height: 1.25;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  width: 100%;
}

.slot-option-card__ingredients {
  font-size: 0.6875rem;
  color: var(--ink-light);
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  width: 100%;
  margin-top: 0.1rem;
}

.slot-option-card__meta {
  font-size: 0.6875rem;
  color: var(--ink-light);
  margin-top: auto;
  padding-top: 0.25rem;
}
</style>
