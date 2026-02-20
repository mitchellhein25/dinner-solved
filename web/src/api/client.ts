import axios from 'axios'

const HOUSEHOLD_KEY = 'dinner_solved_household_id'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
})

apiClient.interceptors.request.use((config) => {
  const householdId = localStorage.getItem(HOUSEHOLD_KEY)
  if (householdId) {
    config.headers['X-Household-ID'] = householdId
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ?? error.message ?? 'Something went wrong'
    return Promise.reject(new Error(String(message)))
  },
)
