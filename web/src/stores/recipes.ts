import { recipesApi } from '@/api/recipes'
import type { RecipeDetail, RecipeListItem } from '@/types'
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useRecipesStore = defineStore('recipes', () => {
  const recipes = ref<RecipeListItem[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const sort = ref<'recent' | 'most_used' | 'alpha' | 'favorites_first'>('recent')
  const favoritesOnly = ref(false)

  async function fetchRecipes() {
    loading.value = true
    error.value = null
    try {
      recipes.value = await recipesApi.getRecipes(sort.value, favoritesOnly.value)
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function toggleFavorite(id: string): Promise<RecipeDetail | null> {
    try {
      const updated = await recipesApi.toggleFavorite(id)
      const idx = recipes.value.findIndex((r) => r.id === id)
      if (idx !== -1) {
        recipes.value[idx] = { ...recipes.value[idx], is_favorite: updated.is_favorite }
      }
      return updated
    } catch (e) {
      error.value = (e as Error).message
      return null
    }
  }

  return { recipes, loading, error, sort, favoritesOnly, fetchRecipes, toggleFavorite }
})
