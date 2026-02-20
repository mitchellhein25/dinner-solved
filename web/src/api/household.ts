import type { HouseholdMember } from '@/types'
import { apiClient } from './client'

export const householdApi = {
  getMembers: () =>
    apiClient.get<{ members: HouseholdMember[] }>('/api/household/members'),

  saveMembers: (members: HouseholdMember[]) =>
    apiClient.post<{ members: HouseholdMember[] }>('/api/household/members', { members }),

  getMember: (id: string) =>
    apiClient.get<HouseholdMember>(`/api/household/members/${id}`),
}
