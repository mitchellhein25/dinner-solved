<script setup lang="ts">
import ChatInput from '@/components/ChatInput.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import SessionPool from '@/components/SessionPool.vue'
import SlotOptionCard from '@/components/SlotOptionCard.vue'
import { recipesApi } from '@/api/recipes'
import { useHouseholdStore } from '@/stores/household'
import { usePlanStore } from '@/stores/plan'
import type { Recipe, RecipeListItem, SlotState } from '@/types'
import { DAY_LABELS, MEAL_TYPE_LABELS } from '@/types'
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const planStore = usePlanStore()
const householdStore = useHouseholdStore()

// Mobile session pool drawer
const poolOpen = ref(false)

const budgetCountdown = ref<string | null>(null)
let countdownTimer: ReturnType<typeof setInterval> | null = null

function updateCountdown() {
  const resetsAt = planStore.budget.resetsAt
  if (!resetsAt) {
    budgetCountdown.value = null
    return
  }
  const seconds = Math.max(0, Math.round((new Date(resetsAt).getTime() - Date.now()) / 1000))
  if (seconds <= 0) {
    budgetCountdown.value = null
    return
  }
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  budgetCountdown.value = mins > 0 ? `${mins}m ${secs}s` : `${secs}s`
}

onMounted(async () => {
  await Promise.all([
    householdStore.fetchMembers(),
    // Ensure template is loaded so we can render blank slots in the initial state
    planStore.template ? Promise.resolve() : planStore.fetchTemplate(),
    // Pre-seed the pool with past recipes (non-fatal if it fails)
    planStore.loadPoolHistory(),
  ])
  updateCountdown()
  countdownTimer = setInterval(updateCountdown, 1000)
})

onUnmounted(() => {
  if (countdownTimer) clearInterval(countdownTimer)
})

// ──────────────────────────────────────────────────────────────────────────
// Slot helpers
// ──────────────────────────────────────────────────────────────────────────

function servingTotal(ss: SlotState): number {
  const total = householdStore.members
    .filter((m) => ss.slot.member_ids.includes(m.id))
    .reduce((s, m) => s + m.serving_size, 0)
  return Math.round(total * ss.slot.days.length * 100) / 100
}

function slotLabel(ss: SlotState): string {
  return ss.slot.days.map((d) => DAY_LABELS[d]).join(', ')
}

const canRegenerateAll = computed(
  () =>
    planStore.budget.remaining >= 1.0 &&
    planStore.slotStates.some((ss) => !ss.locked),
)

// Called from the initial empty state — chat message becomes week context
async function handleInitialChat(message: string) {
  await planStore.suggest(message)
}

// Used in both initial state (Generate) and loaded state (Regenerate All)
async function handleGenerateAll() {
  await planStore.suggest()
}

async function handleRegenerateSlot(slotId: string) {
  await planStore.regenerateSlot(slotId)
}

async function handleChat(message: string) {
  await planStore.refine(message)
}

function handleAssign(recipe: Recipe, slotId: string) {
  planStore.assignFromPool(slotId, recipe)
}

async function handleAssignFromHistory(item: RecipeListItem, slotId: string) {
  try {
    const full = await recipesApi.getRecipe(item.id)
    planStore.assignFromPool(slotId, full)
  } catch {
    // If fetch fails, fall back to assigning with available data (no ingredients)
    planStore.assignFromPool(slotId, {
      id: item.id,
      name: item.name,
      emoji: item.emoji,
      prep_time: item.prep_time,
      ingredients: [],
      key_ingredients: item.key_ingredients,
      is_favorite: item.is_favorite,
    })
  }
}

async function confirm() {
  await planStore.confirm()
  router.push('/grocery')
}
</script>

<template>
  <div class="page">
    <nav class="page__nav">
      <router-link class="btn btn--ghost btn--sm" to="/">← Week</router-link>
      <span class="page__nav-brand">Recipe Suggestions</span>
      <div style="width: 72px"></div>
    </nav>

    <div class="page__body planner-body">
      <!-- Error banner (shown in both states) -->
        <div v-if="planStore.error" class="error-banner">
          {{ planStore.error }}
          <span v-if="planStore.rateLimitError && budgetCountdown"> Resets in {{ budgetCountdown }}.</span>
          <button
            v-if="!planStore.rateLimitError"
            class="btn btn--sm btn--ghost"
            style="margin-left: 0.5rem"
            @click="planStore.suggest()"
          >
            Retry
          </button>
        </div>

        <!-- ══════════════════════════════════════════════════════════════
             INITIAL STATE — no suggestions generated yet
             ══════════════════════════════════════════════════════════════ -->
        <div v-if="planStore.slotStates.length === 0" class="initial-state">
          <!-- Blank slot list -->
          <div v-if="planStore.template" class="slot-list">
            <div
              v-for="slot in planStore.template.slots"
              :key="slot.id"
              class="slot-block slot-block--blank"
            >
              <div class="slot-block__header">
                <div class="slot-block__header-left">
                  <span class="chip">{{ MEAL_TYPE_LABELS[slot.meal_type] }}</span>
                  <span class="slot-block__days">
                    {{ slot.days.map((d) => DAY_LABELS[d]).join(', ') }}
                  </span>
                </div>
              </div>
              <div class="slot-block__blank-body">No recipe chosen yet</div>
            </div>
          </div>

          <!-- Initial prompt -->
          <div class="initial-prompt">
            <p class="initial-prompt__hint">
              Describe what you're after this week, or just generate suggestions.
            </p>
            <ChatInput
              placeholder="e.g. Quick weeknights, something Asian-inspired…"
              :loading="planStore.loading"
              @send="handleInitialChat"
            />
            <button
              class="btn btn--primary btn--full"
              :disabled="planStore.loading || planStore.budget.remaining < 1.0"
              @click="handleGenerateAll"
            >
              <LoadingSpinner v-if="planStore.loading" size="sm" />
              <span v-else>✨ Generate suggestions</span>
            </button>
          </div>
        </div>

        <!-- ══════════════════════════════════════════════════════════════
             LOADED STATE — suggestions available
             ══════════════════════════════════════════════════════════════ -->
        <template v-else>
          <!-- Budget bar -->
          <div class="budget-bar">
            <div class="budget-bar__info">
              <span class="budget-bar__label">
                {{ planStore.budget.remaining.toFixed(1) }} / 3 generations remaining
              </span>
              <span v-if="budgetCountdown" class="budget-bar__reset">
                · resets in {{ budgetCountdown }}
              </span>
            </div>
            <div class="budget-bar__track">
              <div
                class="budget-bar__fill"
                :style="{ width: `${(planStore.budget.remaining / 3) * 100}%` }"
              />
            </div>
          </div>

          <!-- Desktop layout: slots left, pool right -->
          <div class="layout">
            <!-- Left panel: slot list + controls -->
            <main class="layout__main">
              <!-- Top controls -->
              <div class="top-controls">
                <button
                  class="btn btn--ghost btn--sm"
                  :disabled="!canRegenerateAll || planStore.loading"
                  @click="handleGenerateAll"
                >
                  <LoadingSpinner v-if="planStore.loading" size="sm" />
                  <span v-else>↺ Regenerate All</span>
                </button>

                <!-- Mobile: pool toggle -->
                <button
                  class="btn btn--ghost btn--sm pool-toggle"
                  @click="poolOpen = !poolOpen"
                >
                  Browse suggestions
                </button>
              </div>

              <!-- Slot cards -->
              <div class="slot-list">
                <div
                  v-for="ss in planStore.slotStates"
                  :key="ss.slot.id"
                  class="slot-block"
                  :class="{ 'slot-block--locked': ss.locked }"
                >
                  <div class="slot-block__header">
                    <div class="slot-block__header-left">
                      <span class="chip">{{ MEAL_TYPE_LABELS[ss.slot.meal_type] }}</span>
                      <span class="slot-block__days">{{ slotLabel(ss) }}</span>
                      <span class="slot-block__servings">{{ servingTotal(ss) }} srv</span>
                    </div>
                    <button
                      class="lock-btn"
                      :class="{ 'lock-btn--locked': ss.locked }"
                      :title="ss.locked ? 'Unlock slot' : ss.chosenIndex === null ? 'Choose a recipe to lock' : 'Lock slot'"
                      :disabled="!ss.locked && ss.chosenIndex === null"
                      @click="planStore.toggleLock(ss.slot.id)"
                    >
                      {{ ss.locked ? '🔒' : '🔓' }}
                    </button>
                  </div>

                  <div class="slot-block__options">
                    <SlotOptionCard
                      v-for="(recipe, idx) in ss.options"
                      :key="recipe.id"
                      :recipe="recipe"
                      :selected="ss.chosenIndex === idx"
                      :disabled="ss.locked"
                      @select="planStore.chooseOption(ss.slot.id, idx)"
                    />
                  </div>

                  <div class="slot-block__footer">
                    <button
                      class="btn btn--ghost btn--sm"
                      :disabled="ss.locked || ss.regenerating || planStore.budget.remaining < 0.5"
                      @click="handleRegenerateSlot(ss.slot.id)"
                    >
                      <LoadingSpinner v-if="ss.regenerating" size="sm" />
                      <span v-else>↺ Regenerate this slot</span>
                    </button>
                  </div>
                </div>
              </div>

              <!-- Chat refine -->
              <div class="chat-section">
                <p class="chat-section__hint">
                  Not quite right? Ask to swap a recipe, change a cuisine, or make it lighter.
                  Locked slots won't be changed.
                </p>
                <ChatInput :loading="planStore.chatLoading" @send="handleChat" />
              </div>

              <!-- Confirm -->
              <button
                class="btn btn--primary btn--full confirm-btn"
                :disabled="!planStore.allSlotsChosen || planStore.loading"
                @click="confirm"
              >
                Confirm Plan & See Grocery List →
              </button>
            </main>

            <!-- Right panel: session pool (desktop only) -->
            <aside class="layout__pool">
              <SessionPool
                :recipes="planStore.sessionPool"
                :slot-states="planStore.slotStates"
                :history-items="planStore.poolHistory"
                @assign="handleAssign"
                @assign-from-history="handleAssignFromHistory"
              />
            </aside>
          </div>

          <!-- Mobile bottom drawer for session pool -->
          <Teleport to="body">
            <div v-if="poolOpen" class="drawer-backdrop" @click.self="poolOpen = false">
              <div class="drawer">
                <div class="drawer__handle-bar" @click="poolOpen = false" />
                <SessionPool
                  :recipes="planStore.sessionPool"
                  :slot-states="planStore.slotStates"
                  :history-items="planStore.poolHistory"
                  @assign="handleAssign"
                  @assign-from-history="handleAssignFromHistory"
                />
              </div>
            </div>
          </Teleport>
        </template>
    </div>
  </div>
</template>

<style scoped>
/* ─── Wide container for this page ─── */
.planner-body {
  width: 95%;
  margin: 0 auto;
}

/* ─── Error banner ─── */
.error-banner {
  background: color-mix(in srgb, red 10%, var(--card-bg));
  border: 1px solid color-mix(in srgb, red 30%, transparent);
  border-radius: var(--radius);
  padding: 0.625rem 1rem;
  font-size: 0.875rem;
  color: var(--ink);
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.25rem;
}

/* ─── Budget bar ─── */
.budget-bar {
  margin-bottom: 1rem;
}
.budget-bar__info {
  display: flex;
  gap: 0.25rem;
  font-size: 0.8125rem;
  color: var(--ink-light);
  margin-bottom: 0.25rem;
}
.budget-bar__label {
  font-weight: 500;
}
.budget-bar__reset {
  color: var(--ink-light);
}
.budget-bar__track {
  height: 4px;
  background: var(--border);
  border-radius: 99px;
  overflow: hidden;
}
.budget-bar__fill {
  height: 100%;
  background: var(--accent);
  border-radius: 99px;
  transition: width 0.4s ease;
}

/* ─── Initial state ─── */
.initial-state {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.slot-block--blank .slot-block__blank-body {
  padding: 1.25rem 1rem;
  font-size: 0.875rem;
  color: var(--ink-light);
  font-style: italic;
  text-align: center;
}

.initial-prompt {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-width: 36rem;
  margin-left: auto;
  margin-right: auto;
}

.initial-prompt__hint {
  font-size: 0.875rem;
  color: var(--ink-light);
}

/* ─── Layout ─── */
.layout {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

@media (min-width: 960px) {
  .layout {
    display: grid;
    grid-template-columns: 1fr 30%;
    gap: 2rem;
    align-items: start;
  }
}

.layout__pool {
  display: none;
}

@media (min-width: 960px) {
  .layout__pool {
    display: block;
    position: sticky;
    top: 1rem;
    max-height: calc(100vh - 4rem);
    overflow-y: auto;
    overflow-x: hidden;
    min-width: 0;
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem;
  }
}

/* ─── Top controls ─── */
.top-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.pool-toggle {
  display: inline-flex;
}

@media (min-width: 960px) {
  .pool-toggle {
    display: none;
  }
}

/* ─── Slot list ─── */
.slot-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.slot-block {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  overflow: clip;
}

.slot-block--locked {
  opacity: 0.85;
}

.slot-block__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.5rem 0.875rem;
  background: var(--cream);
  border-bottom: 1px solid var(--border);
}

.slot-block__header-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.slot-block__days {
  font-size: 0.8125rem;
  color: var(--ink-light);
}

.slot-block__servings {
  font-size: 0.75rem;
  color: var(--ink-light);
}

.lock-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  padding: 0.25rem;
  opacity: 0.6;
  transition: opacity 0.15s;
  flex-shrink: 0;
}

.lock-btn:hover:not(:disabled) {
  opacity: 1;
}

.lock-btn--locked {
  opacity: 1;
}

.lock-btn:disabled {
  cursor: not-allowed;
  opacity: 0.3;
}

/* Mobile: horizontal scroll so cards stay legible. Show ~2 cards + peek of 3rd. */
.slot-block__options {
  display: flex;
  flex-direction: row;
  gap: 0.5rem;
  padding: 0.75rem;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  -webkit-overflow-scrolling: touch;
  /* Hide scrollbar visually but keep it functional */
  scrollbar-width: none;
}
.slot-block__options::-webkit-scrollbar {
  display: none;
}
.slot-block__options > * {
  flex: 0 0 calc(50% - 1.5rem); /* ~2 cards visible, peek of 3rd */
  scroll-snap-align: start;
  min-width: 8rem;
}

/* Tablet and up: fixed 3-column grid, no scroll */
@media (min-width: 560px) {
  .slot-block__options {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    overflow-x: visible;
    scroll-snap-type: none;
  }
  .slot-block__options > * {
    flex: none;
    min-width: 0;
  }
}

.slot-block__footer {
  padding: 0 0.75rem 0.75rem;
  display: flex;
  justify-content: center;
}

/* ─── Chat ─── */
.chat-section {
  margin-bottom: 1.25rem;
}
.chat-section__hint {
  font-size: 0.875rem;
  color: var(--ink-light);
  margin-bottom: 0.5rem;
}

/* ─── Confirm ─── */
.confirm-btn {
  margin-top: 0.5rem;
  max-width: 28rem;
  margin-left: auto;
  margin-right: auto;
  display: block;
}

/* ─── Mobile drawer ─── */
.drawer-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 100;
  display: flex;
  align-items: flex-end;
}

.drawer {
  background: var(--card-bg);
  border-top-left-radius: calc(var(--radius) * 2);
  border-top-right-radius: calc(var(--radius) * 2);
  padding: 0.75rem 1rem 2rem;
  width: 100%;
  max-height: 70vh;
  overflow-y: auto;
}

.drawer__handle-bar {
  width: 2.5rem;
  height: 4px;
  background: var(--border);
  border-radius: 99px;
  margin: 0 auto 0.75rem;
  cursor: pointer;
}
</style>
