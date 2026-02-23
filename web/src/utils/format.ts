/**
 * Common cooking fractions in ascending order: [decimal value, unicode symbol]
 * Covers everything from ⅛ to ⅞ in standard culinary increments.
 */
const FRACTIONS: Array<[number, string]> = [
  [1 / 8, '⅛'],
  [1 / 4, '¼'],
  [1 / 3, '⅓'],
  [3 / 8, '⅜'],
  [1 / 2, '½'],
  [5 / 8, '⅝'],
  [2 / 3, '⅔'],
  [3 / 4, '¾'],
  [7 / 8, '⅞'],
]

/** Snap threshold — decimal parts within 1/16 of a known fraction are rounded to it. */
const TOLERANCE = 1 / 16 // 0.0625

/**
 * Format a decimal quantity as a human-friendly fraction string.
 *
 * Examples:
 *   1.0   → "1"
 *   0.5   → "½"
 *   1.5   → "1½"
 *   0.333 → "⅓"
 *   2.75  → "2¾"
 *   0.1   → "⅛"   (rounds to nearest common fraction)
 *   14.2  → "14¼" (rounds to nearest common fraction)
 *
 * Decimals that don't snap to any fraction within TOLERANCE are shown
 * as compact decimals (e.g. 0.17 → "0.17").
 */
export function formatQuantity(value: number): string {
  if (value <= 0) return '0'

  let whole = Math.floor(value)
  let decimal = value - whole

  // Snap trailing decimal to 0 or 1 if it's very close
  if (decimal < TOLERANCE) return whole === 0 ? '0' : String(whole)
  if (decimal >= 1 - TOLERANCE) return String(whole + 1)

  // Find the nearest common fraction
  let bestSymbol = ''
  let bestDiff = Infinity
  for (const [frac, symbol] of FRACTIONS) {
    const diff = Math.abs(decimal - frac)
    if (diff < bestDiff) {
      bestDiff = diff
      bestSymbol = symbol
    }
  }

  if (bestDiff <= TOLERANCE) {
    return whole > 0 ? `${whole}${bestSymbol}` : bestSymbol
  }

  // No close fraction — show as a compact decimal
  const compact = parseFloat(value.toFixed(2))
  return String(compact)
}
