import type { GroceryListItem } from '@/types'
import { apiClient } from './client'

export interface GroceryListResponse {
  week_start_date: string
  items: GroceryListItem[]
}

export const groceryApi = {
  getList: (weekStartDate: string) =>
    apiClient.get<GroceryListResponse>(`/api/grocery/${weekStartDate}`),

  exportCsv: (weekStartDate: string) =>
    apiClient.post<{ result: string }>('/api/grocery/export/csv', {
      week_start_date: weekStartDate,
    }),

  exportSheets: (weekStartDate: string) =>
    apiClient.post<{ result: string }>('/api/grocery/export/sheets', {
      week_start_date: weekStartDate,
    }),

  async downloadGroceryPdf(weekStartDate: string): Promise<void> {
    const res = await apiClient.get(`/api/grocery/${weekStartDate}/export/pdf`, {
      responseType: 'blob',
    })
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = `grocery-list-${weekStartDate}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  },
}
