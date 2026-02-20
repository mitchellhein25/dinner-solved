import { groceryApi } from '@/api/grocery'
import { planApi } from '@/api/plan'
import type { GroceryListItem, MealPlanTemplate, Recipe, RecipeSuggestion } from '@/types'
import { getWeekStart } from '@/utils/date'
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const usePlanStore = defineStore('plan', () => {
  const template = ref<MealPlanTemplate | null>(null)
  const suggestions = ref<RecipeSuggestion[]>([])
  const groceryItems = ref<GroceryListItem[]>([])
  const weekStartDate = ref<string>(getWeekStart())
  const loading = ref(false)
  const chatLoading = ref(false)
  const error = ref<string | null>(null)

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

  async function suggest(weekContext?: string) {
    loading.value = true
    error.value = null
    try {
      const res = await planApi.suggest(weekContext)
      suggestions.value = res.data.suggestions
    } catch (e) {
      error.value = (e as Error).message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function refine(userMessage: string, slotIdToRefine?: string) {
    chatLoading.value = true
    error.value = null
    try {
      // Build existing_assignments map: slot_id -> recipe
      const existing: Record<string, Recipe> = {}
      for (const s of suggestions.value) {
        existing[s.slot.id] = s.recipe
      }
      const res = await planApi.refine(existing, userMessage, slotIdToRefine)
      suggestions.value = res.data.suggestions
    } catch (e) {
      error.value = (e as Error).message
      throw e
    } finally {
      chatLoading.value = false
    }
  }

  async function confirm() {
    loading.value = true
    error.value = null
    try {
      await planApi.confirm(weekStartDate.value, suggestions.value)
    } catch (e) {
      error.value = (e as Error).message
      throw e
    } finally {
      loading.value = false
    }
  }

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

  return {
    template,
    suggestions,
    groceryItems,
    weekStartDate,
    loading,
    chatLoading,
    error,
    fetchTemplate,
    saveTemplate,
    suggest,
    refine,
    confirm,
    fetchGroceryList,
  }
})
