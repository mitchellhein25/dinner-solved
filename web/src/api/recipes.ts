import type { RecipeDetail, RecipeListItem } from '@/types'
import { apiClient } from './client'

export const recipesApi = {
  async getRecipes(sort = 'recent', favoritesOnly = false): Promise<RecipeListItem[]> {
    const res = await apiClient.get('/api/recipes', {
      params: { sort, favorites_only: favoritesOnly },
    })
    return res.data
  },

  async getRecipe(id: string): Promise<RecipeDetail> {
    const res = await apiClient.get(`/api/recipes/${id}`)
    return res.data
  },

  async toggleFavorite(id: string): Promise<RecipeDetail> {
    const res = await apiClient.patch(`/api/recipes/${id}/favorite`)
    return res.data
  },
}
