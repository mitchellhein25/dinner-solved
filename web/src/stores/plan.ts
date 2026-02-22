import { groceryApi } from '@/api/grocery'
import { planApi } from '@/api/plan'
import type { SlotOptionsResponse } from '@/api/plan'
import { recipesApi } from '@/api/recipes'
import type {
  GenerationBudget,
  GroceryListItem,
  MealPlanTemplate,
  Recipe,
  RecipeListItem,
  RecipeSuggestion,
  SlotState,
} from '@/types'
import { getWeekStart } from '@/utils/date'
import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'

// ─── Persistence helpers ──────────────────────────────────────────────────────

function sessionKey(week: string) {
  return `plan-session-${week}`
}

function localKey(week: string) {
  return `plan-saved-${week}`
}

interface PersistedState {
  slotStates: Omit<SlotState, 'regenerating'>[]
  sessionPool: Recipe[]
}

function serializeState(states: SlotState[], pool: Recipe[]): string {
  const data: PersistedState = {
    slotStates: states.map(({ regenerating: _r, ...rest }) => rest),
    sessionPool: pool,
  }
  return JSON.stringify(data)
}

function parseState(raw: string | null): PersistedState | null {
  if (!raw) return null
  try {
    return JSON.parse(raw) as PersistedState
  } catch {
    return null
  }
}

// ─────────────────────────────────────────────────────────────────────────────

export const usePlanStore = defineStore('plan', () => {
  const template = ref<MealPlanTemplate | null>(null)
  const slotStates = ref<SlotState[]>([])
  const sessionPool = ref<Recipe[]>([])
  const poolHistory = ref<RecipeListItem[]>([])
  const budget = ref<GenerationBudget>({ remaining: 3, resetsAt: null })
  const groceryItems = ref<GroceryListItem[]>([])
  const weekStartDate = ref<string>(getWeekStart())
  const loading = ref(false)
  const chatLoading = ref(false)
  const error = ref<string | null>(null)
  const rateLimitError = ref<{ retryAfterSeconds: number } | null>(null)

  // Auto-save slotStates to sessionStorage on any change
  watch(
    slotStates,
    (states) => {
      if (states.length > 0) {
        try {
          sessionStorage.setItem(sessionKey(weekStartDate.value), serializeState(states, sessionPool.value))
        } catch {
          // Storage might be full or unavailable — non-fatal
        }
      }
    },
    { deep: true },
  )

  // ──────────────────────────────────────────────────────────────────────────
  // Helpers
  // ──────────────────────────────────────────────────────────────────────────

  function seedPool(recipes: Recipe[]) {
    const seen = new Set(sessionPool.value.map((r) => r.name))
    for (const r of recipes) {
      if (!seen.has(r.name)) {
        sessionPool.value.push(r)
        seen.add(r.name)
      }
    }
  }

  function applyBudget(data: SlotOptionsResponse) {
    budget.value = {
      remaining: data.budget_remaining,
      resetsAt: data.budget_resets_at,
    }
    for (const so of data.slot_options) {
      seedPool(so.options)
    }
  }

  function handleRateLimitError(e: any) {
    const detail = e?.response?.data?.detail
    rateLimitError.value = {
      retryAfterSeconds: detail?.retry_after_seconds ?? 600,
    }
    error.value = 'Rate limit reached — please wait before generating again.'
  }

  // ──────────────────────────────────────────────────────────────────────────
  // Session persistence
  // ──────────────────────────────────────────────────────────────────────────

  /**
   * Try to restore slotStates from sessionStorage, then fall back to localStorage.
   * Returns true if state was restored (caller can skip the initial suggest() call).
   */
  function restoreSession(): boolean {
    const week = weekStartDate.value
    const raw = sessionStorage.getItem(sessionKey(week)) ?? localStorage.getItem(localKey(week))
    const saved = parseState(raw)
    if (!saved || saved.slotStates.length === 0) return false

    slotStates.value = saved.slotStates.map((s) => ({ ...s, regenerating: false }))
    sessionPool.value = saved.sessionPool ?? []
    return true
  }

  /**
   * Initialise empty slot states from the template so the session pool can
   * assign recipes before AI suggestions are generated.
   */
  function initFromTemplate() {
    if (!template.value || slotStates.value.length > 0) return
    slotStates.value = template.value.slots.map((slot) => ({
      slot,
      options: [],
      chosenIndex: null,
      locked: false,
      regenerating: false,
    }))
  }

  /**
   * Persist current state to localStorage so it survives tab closes.
   */
  function saveProgress() {
    if (slotStates.value.length === 0) return
    try {
      localStorage.setItem(localKey(weekStartDate.value), serializeState(slotStates.value, sessionPool.value))
    } catch {
      // Non-fatal
    }
  }

  /**
   * Clear saved progress from both storages (called after confirm or "Start over").
   */
  function clearProgress() {
    const week = weekStartDate.value
    sessionStorage.removeItem(sessionKey(week))
    localStorage.removeItem(localKey(week))
  }

  /**
   * Reset all suggestion state and clear persisted progress.
   */
  function startOver() {
    slotStates.value = []
    sessionPool.value = []
    error.value = null
    rateLimitError.value = null
    clearProgress()
    initFromTemplate()
  }

  // ──────────────────────────────────────────────────────────────────────────
  // Template
  // ──────────────────────────────────────────────────────────────────────────

  async function fetchTemplate() {
    loading.value = true
    error.value = null
    try {
      const res = await planApi.getTemplate()
      template.value = res.data
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function saveTemplate(tpl: MealPlanTemplate) {
    loading.value = true
    error.value = null
    try {
      const res = await planApi.saveTemplate(tpl)
      template.value = res.data
    } catch (e) {
      error.value = (e as Error).message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function loadPoolHistory() {
    try {
      poolHistory.value = await recipesApi.getRecipes('recent', false)
    } catch {
      // Non-fatal — pool history is a convenience feature
    }
  }

  // ──────────────────────────────────────────────────────────────────────────
  // Suggestion actions
  // ──────────────────────────────────────────────────────────────────────────

  async function suggest(weekContext?: string) {
    loading.value = true
    error.value = null
    rateLimitError.value = null
    try {
      const res = await planApi.suggest(weekContext)
      const data = res.data
      slotStates.value = data.slot_options.map((so) => ({
        slot: so.slot,
        options: so.options,
        chosenIndex: null,
        locked: false,
        regenerating: false,
      }))
      applyBudget(data)
    } catch (e: any) {
      if (e?.response?.status === 429) {
        handleRateLimitError(e)
      } else {
        error.value = (e as Error).message
      }
      throw e
    } finally {
      loading.value = false
    }
  }

  async function refine(userMessage: string) {
    chatLoading.value = true
    error.value = null
    rateLimitError.value = null
    try {
      const lockedSlotIds = slotStates.value
        .filter((s) => s.locked)
        .map((s) => s.slot.id)

      const existingAssignments: Record<string, Recipe> = {}
      for (const ss of slotStates.value) {
        if (ss.chosenIndex !== null) {
          existingAssignments[ss.slot.id] = ss.options[ss.chosenIndex]
        }
      }

      const res = await planApi.refine(existingAssignments, userMessage, lockedSlotIds)
      const data = res.data

      // Merge: update only the unlocked slots returned by the API
      for (const so of data.slot_options) {
        const idx = slotStates.value.findIndex((ss) => ss.slot.id === so.slot.id)
        if (idx !== -1) {
          slotStates.value[idx] = {
            ...slotStates.value[idx],
            options: so.options,
            chosenIndex: null, // reset choice after refine
          }
        }
      }
      applyBudget(data)
    } catch (e: any) {
      if (e?.response?.status === 429) {
        handleRateLimitError(e)
      } else {
        error.value = (e as Error).message
      }
      throw e
    } finally {
      chatLoading.value = false
    }
  }

  async function regenerateSlot(slotId: string) {
    const idx = slotStates.value.findIndex((ss) => ss.slot.id === slotId)
    if (idx === -1 || slotStates.value[idx].locked) return

    error.value = null
    rateLimitError.value = null
    slotStates.value[idx] = { ...slotStates.value[idx], regenerating: true }

    try {
      const existingChosen: Record<string, Recipe> = {}
      for (const ss of slotStates.value) {
        if (ss.chosenIndex !== null) {
          existingChosen[ss.slot.id] = ss.options[ss.chosenIndex]
        }
      }

      const res = await planApi.suggestSlot(slotId, existingChosen)
      const data = res.data

      if (data.slot_options.length > 0) {
        slotStates.value[idx] = {
          ...slotStates.value[idx],
          options: data.slot_options[0].options,
          chosenIndex: null,
          regenerating: false,
        }
      }
      applyBudget(data)
    } catch (e: any) {
      if (e?.response?.status === 429) {
        handleRateLimitError(e)
      } else {
        error.value = (e as Error).message
      }
      slotStates.value[idx] = { ...slotStates.value[idx], regenerating: false }
      throw e
    }
  }

  // ──────────────────────────────────────────────────────────────────────────
  // Slot state mutations
  // ──────────────────────────────────────────────────────────────────────────

  function chooseOption(slotId: string, optionIndex: number) {
    const ss = slotStates.value.find((s) => s.slot.id === slotId)
    if (ss && !ss.locked) {
      ss.chosenIndex = optionIndex
    }
  }

  function toggleLock(slotId: string) {
    const ss = slotStates.value.find((s) => s.slot.id === slotId)
    if (!ss) return
    // Cannot lock without a chosen recipe
    if (!ss.locked && ss.chosenIndex === null) return
    ss.locked = !ss.locked
  }

  /**
   * Assign a recipe from the session pool to a slot.
   * If the recipe is already in the slot's options, select it; otherwise append it.
   */
  function assignFromPool(slotId: string, recipe: Recipe) {
    const ss = slotStates.value.find((s) => s.slot.id === slotId)
    if (!ss || ss.locked) return

    const existingIdx = ss.options.findIndex((r) => r.name === recipe.name)
    if (existingIdx !== -1) {
      ss.chosenIndex = existingIdx
    } else {
      ss.options.push(recipe)
      ss.chosenIndex = ss.options.length - 1
    }
  }

  // ──────────────────────────────────────────────────────────────────────────
  // Confirm
  // ──────────────────────────────────────────────────────────────────────────

  async function confirm() {
    loading.value = true
    error.value = null
    try {
      const suggestions: RecipeSuggestion[] = slotStates.value
        .filter((ss) => ss.chosenIndex !== null)
        .map((ss) => ({
          slot: ss.slot,
          recipe: ss.options[ss.chosenIndex!],
        }))
      await planApi.confirm(weekStartDate.value, suggestions)
      clearProgress()
    } catch (e) {
      error.value = (e as Error).message
      throw e
    } finally {
      loading.value = false
    }
  }

  // ──────────────────────────────────────────────────────────────────────────
  // Grocery list
  // ──────────────────────────────────────────────────────────────────────────

  async function fetchGroceryList() {
    loading.value = true
    error.value = null
    try {
      const res = await groceryApi.getList(weekStartDate.value)
      groceryItems.value = res.data.items
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  // ──────────────────────────────────────────────────────────────────────────
  // Computed
  // ──────────────────────────────────────────────────────────────────────────

  const allSlotsChosen = computed(() =>
    slotStates.value.length > 0 && slotStates.value.every((ss) => ss.chosenIndex !== null),
  )

  /** True once AI options have been generated for at least one slot. */
  const hasGeneratedOptions = computed(() =>
    slotStates.value.some((ss) => ss.options.length > 0),
  )

  return {
    template,
    slotStates,
    sessionPool,
    poolHistory,
    budget,
    groceryItems,
    weekStartDate,
    loading,
    chatLoading,
    error,
    rateLimitError,
    allSlotsChosen,
    hasGeneratedOptions,
    fetchTemplate,
    saveTemplate,
    loadPoolHistory,
    restoreSession,
    initFromTemplate,
    saveProgress,
    startOver,
    suggest,
    refine,
    regenerateSlot,
    chooseOption,
    toggleLock,
    assignFromPool,
    confirm,
    fetchGroceryList,
  }
})
