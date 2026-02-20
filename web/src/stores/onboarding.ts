import { defineStore } from 'pinia'
import { ref } from 'vue'

const ONBOARDING_KEY = 'dinner_solved_onboarded'

export const useOnboardingStore = defineStore('onboarding', () => {
  const isComplete = ref(localStorage.getItem(ONBOARDING_KEY) === 'true')

  function complete() {
    isComplete.value = true
    localStorage.setItem(ONBOARDING_KEY, 'true')
  }

  function reset() {
    isComplete.value = false
    localStorage.removeItem(ONBOARDING_KEY)
  }

  return { isComplete, complete, reset }
})
