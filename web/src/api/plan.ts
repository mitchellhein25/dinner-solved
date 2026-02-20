import type { MealPlanTemplate, Recipe, RecipeSuggestion, WeeklyPlan } from '@/types'
import { apiClient } from './client'

export const planApi = {
  getTemplate: () => apiClient.get<MealPlanTemplate>('/api/template'),

  saveTemplate: (template: MealPlanTemplate) =>
    apiClient.post<MealPlanTemplate>('/api/template', { template }),

  suggest: (weekContext?: string) =>
    apiClient.post<{ suggestions: RecipeSuggestion[] }>('/api/plan/suggest', {
      week_context: weekContext ?? null,
    }),

  refine: (
    existingAssignments: Record<string, Recipe>,
    userMessage: string,
    slotIdToRefine?: string,
  ) =>
    apiClient.post<{ suggestions: RecipeSuggestion[] }>('/api/plan/refine', {
      existing_assignments: existingAssignments,
      user_message: userMessage,
      slot_id_to_refine: slotIdToRefine ?? null,
    }),

  confirm: (weekStartDate: string, suggestions: RecipeSuggestion[]) =>
    apiClient.post<WeeklyPlan>('/api/plan/confirm', {
      week_start_date: weekStartDate,
      suggestions,
    }),
}
