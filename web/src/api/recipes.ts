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

  async generateInstructions(id: string): Promise<RecipeDetail> {
    const res = await apiClient.post(`/api/recipes/${id}/instructions`)
    return res.data
  },

  async toggleFavorite(id: string): Promise<RecipeDetail> {
    const res = await apiClient.patch(`/api/recipes/${id}/favorite`)
    return res.data
  },

  async updateRecipe(id: string, name: string, emoji: string): Promise<RecipeDetail> {
    const res = await apiClient.patch(`/api/recipes/${id}`, { name, emoji })
    return res.data
  },

  async deleteRecipe(id: string): Promise<void> {
    await apiClient.delete(`/api/recipes/${id}`)
  },

  getRecipePdfUrl(id: string): string {
    return `/api/recipes/${id}/export/pdf`
  },
}
