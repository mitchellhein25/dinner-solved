<script setup lang="ts">
import type { Recipe, RecipeListItem, SlotState } from '@/types'
import { computed, ref } from 'vue'

const props = defineProps<{
  recipes: Recipe[]
  slotStates: SlotState[]
  historyItems?: RecipeListItem[]
}>()

const emit = defineEmits<{
  assign: [recipe: Recipe, slotId: string]
  assignFromHistory: [item: RecipeListItem, slotId: string]
}>()

// ── Search & filter ────────────────────────────────────────────────────────

const search = ref('')
const favoritesOnly = ref(false)

const filteredPool = computed(() => {
  const q = search.value.trim().toLowerCase()
  return props.recipes.filter((r) => !q || r.name.toLowerCase().includes(q))
})

const sessionNames = computed(() => new Set(props.recipes.map((r) => r.name.toLowerCase())))

const filteredHistory = computed(() => {
  if (!props.historyItems) return []
  const q = search.value.trim().toLowerCase()
  return props.historyItems.filter((r) => {
    if (sessionNames.value.has(r.name.toLowerCase())) return false // already in session pool
    if (favoritesOnly.value && !r.is_favorite) return false
    if (q && !r.name.toLowerCase().includes(q)) return false
    return true
  })
})

// ── Popover ────────────────────────────────────────────────────────────────

const popoverRecipe = ref<Recipe | null>(null)
const popoverHistoryItem = ref<RecipeListItem | null>(null)
const popoverOpen = ref(false)

function closePopover() {
  popoverOpen.value = false
  popoverRecipe.value = null
  popoverHistoryItem.value = null
}

function assign(slotId: string) {
  if (popoverRecipe.value) {
    emit('assign', popoverRecipe.value, slotId)
  } else if (popoverHistoryItem.value) {
    emit('assignFromHistory', popoverHistoryItem.value, slotId)
  }
  closePopover()
}

const assignableSlots = computed(() => props.slotStates.filter((ss) => !ss.locked))

function handlePoolClick(recipe: Recipe) {
  if (assignableSlots.value.length === 0) return
  if (assignableSlots.value.length === 1) {
    emit('assign', recipe, assignableSlots.value[0].slot.id)
    return
  }
  popoverRecipe.value = recipe
  popoverHistoryItem.value = null
  popoverOpen.value = true
}

function handleHistoryClick(item: RecipeListItem) {
  if (assignableSlots.value.length === 0) return
  if (assignableSlots.value.length === 1) {
    emit('assignFromHistory', item, assignableSlots.value[0].slot.id)
    return
  }
  popoverHistoryItem.value = item
  popoverRecipe.value = null
  popoverOpen.value = true
}

function isChosen(name: string): boolean {
  return props.slotStates.some(
    (ss) => ss.chosenIndex !== null && ss.options[ss.chosenIndex]?.name === name,
  )
}
</script>

<template>
  <div class="session-pool">
    <!-- Search bar -->
    <input
      v-model="search"
      class="input pool-search"
      type="search"
      placeholder="🔍 Search recipes…"
    />

    <!-- Seen this session -->
    <div class="pool-section">
      <h3 class="pool-section__title">Seen this session</h3>
      <div v-if="filteredPool.length === 0" class="pool-empty">
        {{ recipes.length === 0 ? 'Recipes seen this session will appear here.' : 'No matches.' }}
      </div>
      <div v-else class="pool-grid">
        <button
          v-for="recipe in filteredPool"
          :key="recipe.id"
          class="pool-card"
          :class="{ 'pool-card--chosen': isChosen(recipe.name) }"
          :title="`Click to assign: ${recipe.name}`"
          @click="handlePoolClick(recipe)"
        >
          <span class="pool-card__emoji">{{ recipe.emoji }}</span>
          <span class="pool-card__name">{{ recipe.name }}</span>
        </button>
      </div>
    </div>

    <!-- From your history -->
    <div v-if="historyItems !== undefined" class="pool-section">
      <div class="pool-section__header">
        <h3 class="pool-section__title">From your history</h3>
        <button
          class="btn btn--sm fav-toggle"
          :class="favoritesOnly ? 'fav-toggle--active' : ''"
          :title="favoritesOnly ? 'Show all' : 'Show favorites only'"
          @click="favoritesOnly = !favoritesOnly"
        >
          ♥
        </button>
      </div>
      <div v-if="filteredHistory.length === 0" class="pool-empty">
        {{ historyItems.length === 0 ? 'No past recipes yet.' : 'No matches.' }}
      </div>
      <div v-else class="pool-grid">
        <button
          v-for="item in filteredHistory"
          :key="item.id"
          class="pool-card"
          :class="{ 'pool-card--chosen': isChosen(item.name), 'pool-card--favorite': item.is_favorite }"
          :title="`Click to assign: ${item.name}`"
          @click="handleHistoryClick(item)"
        >
          <span class="pool-card__emoji">{{ item.emoji }}</span>
          <span class="pool-card__name">{{ item.name }}</span>
          <span v-if="item.is_favorite" class="pool-card__fav">♥</span>
        </button>
      </div>
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
  gap: 1rem;
}

/* Search */
.pool-search {
  font-size: 0.8125rem;
  padding: 0.4rem 0.625rem;
}

/* Section */
.pool-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.pool-section__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.pool-section__title {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--ink-light);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.pool-empty {
  font-size: 0.8125rem;
  color: var(--ink-light);
  padding: 0.25rem 0;
}

/* Grid */
.pool-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.3rem;
}

/* Card */
.pool-card {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.45rem 0.625rem;
  min-height: 2.25rem;
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
  font-size: 1rem;
  flex-shrink: 0;
}

.pool-card__name {
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}

.pool-card__fav {
  color: #e05c5c;
  font-size: 0.6875rem;
  flex-shrink: 0;
}

/* Favorites toggle */
.fav-toggle {
  padding: 0.2rem 0.5rem;
  font-size: 0.75rem;
  border: 1px solid var(--border);
  background: var(--card-bg);
  color: var(--ink-light);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
  line-height: 1;
}

.fav-toggle:hover {
  border-color: #e05c5c;
  color: #e05c5c;
}

.fav-toggle--active {
  color: #e05c5c;
  border-color: #e05c5c;
  background: #fff5f5;
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
  min-height: 2.75rem;
}

.pool-popover__cancel {
  margin-top: 0.25rem;
  color: var(--ink-light);
}
</style>
