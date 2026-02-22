<script setup lang="ts">
import type { Recipe, SlotState } from '@/types'
import { computed, ref } from 'vue'

const props = defineProps<{
  recipes: Recipe[]
  slotStates: SlotState[]
}>()

const emit = defineEmits<{
  assign: [recipe: Recipe, slotId: string]
}>()

// Slot-picker popover state
const popoverRecipe = ref<Recipe | null>(null)
const popoverOpen = ref(false)

function openPopover(recipe: Recipe) {
  popoverRecipe.value = recipe
  popoverOpen.value = true
}

function closePopover() {
  popoverOpen.value = false
  popoverRecipe.value = null
}

function assign(slotId: string) {
  if (popoverRecipe.value) {
    emit('assign', popoverRecipe.value, slotId)
  }
  closePopover()
}

// Unlocked slots available for assignment
const assignableSlots = computed(() =>
  props.slotStates.filter((ss) => !ss.locked),
)

function handleRecipeClick(recipe: Recipe) {
  if (assignableSlots.value.length === 0) return
  if (assignableSlots.value.length === 1) {
    emit('assign', recipe, assignableSlots.value[0].slot.id)
    return
  }
  openPopover(recipe)
}

function isChosen(recipe: Recipe): boolean {
  return props.slotStates.some(
    (ss) => ss.chosenIndex !== null && ss.options[ss.chosenIndex]?.name === recipe.name,
  )
}
</script>

<template>
  <div class="session-pool">
    <h3 class="session-pool__title">Seen this session</h3>

    <div v-if="recipes.length === 0" class="session-pool__empty">
      Recipes you've seen will appear here.
    </div>

    <div v-else class="session-pool__grid">
      <button
        v-for="recipe in recipes"
        :key="recipe.id"
        class="pool-card"
        :class="{ 'pool-card--chosen': isChosen(recipe) }"
        :title="`Click to assign: ${recipe.name}`"
        @click="handleRecipeClick(recipe)"
      >
        <span class="pool-card__emoji">{{ recipe.emoji }}</span>
        <span class="pool-card__name">{{ recipe.name }}</span>
      </button>
    </div>

    <!-- Slot-picker popover -->
    <Teleport to="body">
      <div v-if="popoverOpen" class="pool-popover-backdrop" @click.self="closePopover">
        <div class="pool-popover">
          <p class="pool-popover__title">Assign to which slot?</p>
          <button
            v-for="ss in assignableSlots"
            :key="ss.slot.id"
            class="btn btn--ghost pool-popover__slot"
            @click="assign(ss.slot.id)"
          >
            {{ ss.slot.name }}
          </button>
          <button class="btn btn--ghost btn--sm pool-popover__cancel" @click="closePopover">
            Cancel
          </button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.session-pool {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.session-pool__title {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--ink-light);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.session-pool__empty {
  font-size: 0.8125rem;
  color: var(--ink-light);
  padding: 0.5rem 0;
}

.session-pool__grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.375rem;
}

.pool-card {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  min-height: 2.5rem; /* comfortable tap target on mobile */
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: calc(var(--radius) * 0.75);
  cursor: pointer;
  text-align: left;
  font-size: 0.8125rem;
  transition: border-color 0.15s;
  width: 100%;
}

.pool-card:hover {
  border-color: var(--accent);
}

.pool-card--chosen {
  border-color: var(--accent);
  background: color-mix(in srgb, var(--accent) 8%, var(--card-bg));
}

.pool-card__emoji {
  font-size: 1.125rem;
  flex-shrink: 0;
}

.pool-card__name {
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Popover */
.pool-popover-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pool-popover {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 14rem;
}

.pool-popover__title {
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.pool-popover__slot {
  justify-content: flex-start;
  min-height: 2.75rem; /* comfortable tap target */
}

.pool-popover__cancel {
  margin-top: 0.25rem;
  color: var(--ink-light);
}
</style>
