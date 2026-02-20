import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

const HOUSEHOLD_KEY = 'dinner_solved_household_id'
const ONBOARDING_KEY = 'dinner_solved_onboarded'

export const useAuthStore = defineStore('auth', () => {
  const householdId = ref<string | null>(localStorage.getItem(HOUSEHOLD_KEY))

  const isAuthenticated = computed(() => householdId.value !== null)

  function setHousehold(id: string) {
    householdId.value = id
    localStorage.setItem(HOUSEHOLD_KEY, id)
  }

  function logout() {
    householdId.value = null
    localStorage.removeItem(HOUSEHOLD_KEY)
    localStorage.removeItem(ONBOARDING_KEY)
  }

  return { householdId, isAuthenticated, setHousehold, logout }
})
