/** Returns the ISO date string (YYYY-MM-DD) of the Monday of the given date's week. */
export function getWeekStart(date = new Date()): string {
  const d = new Date(date)
  const day = d.getDay()
  const diff = day === 0 ? -6 : 1 - day // shift Sunday back 6, otherwise forward to Monday
  d.setDate(d.getDate() + diff)
  return d.toISOString().split('T')[0]
}

export function formatWeekRange(weekStart: string): string {
  const start = new Date(weekStart + 'T00:00:00')
  const end = new Date(start)
  end.setDate(end.getDate() + 6)
  const fmt = (d: Date) =>
    d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  return `${fmt(start)} – ${fmt(end)}`
}
