import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

const HOUSEHOLD_KEY = 'dinner_solved_household_id'
const EMAIL_KEY = 'dinner_solved_email'

export const useAuthStore = defineStore('auth', () => {
  const householdId = ref<string | null>(localStorage.getItem(HOUSEHOLD_KEY))
  const email = ref<string | null>(localStorage.getItem(EMAIL_KEY))

  const isAuthenticated = computed(() => householdId.value !== null)

  function setHousehold(id: string, userEmail: string) {
    householdId.value = id
    email.value = userEmail
    localStorage.setItem(HOUSEHOLD_KEY, id)
    localStorage.setItem(EMAIL_KEY, userEmail)
  }

  function logout() {
    householdId.value = null
    email.value = null
    localStorage.removeItem(HOUSEHOLD_KEY)
    localStorage.removeItem(EMAIL_KEY)
  }

  return { householdId, email, isAuthenticated, setHousehold, logout }
})
