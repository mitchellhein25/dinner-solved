import type { UserPreferences } from '@/types'
import { apiClient } from './client'

export const preferencesApi = {
  get: () => apiClient.get<UserPreferences>('/api/preferences'),

  save: (preferences: UserPreferences) =>
    apiClient.post<UserPreferences>('/api/preferences', { preferences }),
}
