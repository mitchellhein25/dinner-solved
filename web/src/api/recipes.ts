import type { RecipeDetail, RecipeDraft, RecipeListItem } from '@/types'
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

  async downloadRecipePdf(id: string, name: string): Promise<void> {
    const res = await apiClient.get(`/api/recipes/${id}/export/pdf`, {
      responseType: 'blob',
    })
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = `${name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  },

  async importFromUrl(url: string): Promise<RecipeDetail> {
    const res = await apiClient.post('/api/recipes/import', { url })
    return res.data
  },

  async createRecipe(draft: RecipeDraft): Promise<RecipeDetail> {
    const res = await apiClient.post('/api/recipes/', draft)
    return res.data
  },

  async updateRecipeFull(id: string, draft: RecipeDraft): Promise<RecipeDetail> {
    const res = await apiClient.put(`/api/recipes/${id}`, draft)
    return res.data
  },
}
