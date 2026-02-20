import { householdApi } from '@/api/household'
import type { HouseholdMember } from '@/types'
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useHouseholdStore = defineStore('household', () => {
  const members = ref<HouseholdMember[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchMembers() {
    loading.value = true
    error.value = null
    try {
      const res = await householdApi.getMembers()
      members.value = res.data.members
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function saveMembers(updated: HouseholdMember[]) {
    loading.value = true
    error.value = null
    try {
      const res = await householdApi.saveMembers(updated)
      members.value = res.data.members
    } catch (e) {
      error.value = (e as Error).message
      throw e
    } finally {
      loading.value = false
    }
  }

  return { members, loading, error, fetchMembers, saveMembers }
})
