import { apiClient } from './client'

export const authApi = {
  requestLink: (email: string) =>
    apiClient.post('/api/auth/request-link', { email }),

  verifyToken: (token: string) =>
    apiClient.post<{ household_id: string }>('/api/auth/verify', { token }),
}
