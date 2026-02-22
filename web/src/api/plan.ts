import type { ConfirmedPlan, MealPlanTemplate, MealSlot, Recipe, RecipeSuggestion, WeeklyPlan } from '@/types'
import { apiClient } from './client'

export interface SlotOptionsData {
  slot: MealSlot
  options: Recipe[]
}

export interface SlotOptionsResponse {
  slot_options: SlotOptionsData[]
  budget_remaining: number
  budget_resets_at: string | null
}

export const planApi = {
  getTemplate: () => apiClient.get<MealPlanTemplate>('/api/template'),

  saveTemplate: (template: MealPlanTemplate) =>
    apiClient.post<MealPlanTemplate>('/api/template', { template }),

  suggest: (weekContext?: string) =>
    apiClient.post<SlotOptionsResponse>('/api/plan/suggest', {
      week_context: weekContext ?? null,
    }),

  refine: (
    existingAssignments: Record<string, Recipe>,
    userMessage: string,
    lockedSlotIds: string[] = [],
  ) =>
    apiClient.post<SlotOptionsResponse>('/api/plan/refine', {
      existing_assignments: existingAssignments,
      user_message: userMessage,
      locked_slot_ids: lockedSlotIds,
    }),

  suggestSlot: (
    slotId: string,
    existingChosen: Record<string, Recipe>,
    weekContext?: string,
  ) =>
    apiClient.post<SlotOptionsResponse>('/api/plan/suggest-slot', {
      slot_id: slotId,
      existing_chosen: existingChosen,
      week_context: weekContext ?? null,
    }),

  confirm: (weekStartDate: string, suggestions: RecipeSuggestion[]) =>
    apiClient.post<WeeklyPlan>('/api/plan/confirm', {
      week_start_date: weekStartDate,
      suggestions,
    }),

  getConfirmedPlan: (weekStartDate: string) =>
    apiClient.get<ConfirmedPlan>(`/api/plan/${weekStartDate}`),

  getPlanPdfUrl: (weekStartDate: string): string => `/api/plan/${weekStartDate}/export/pdf`,
}
