import { describe, expect, it } from 'vitest'
import { formatQuantity } from './format'

describe('formatQuantity', () => {
  it('returns "0" for zero', () => {
    expect(formatQuantity(0)).toBe('0')
  })

  it('returns "0" for negative values', () => {
    expect(formatQuantity(-1)).toBe('0')
  })

  it('formats whole numbers as integers', () => {
    expect(formatQuantity(1)).toBe('1')
    expect(formatQuantity(2)).toBe('2')
    expect(formatQuantity(14)).toBe('14')
  })

  it('formats exact common fractions', () => {
    expect(formatQuantity(0.125)).toBe('⅛')
    expect(formatQuantity(0.25)).toBe('¼')
    expect(formatQuantity(1 / 3)).toBe('⅓')
    expect(formatQuantity(0.375)).toBe('⅜')
    expect(formatQuantity(0.5)).toBe('½')
    expect(formatQuantity(0.625)).toBe('⅝')
    expect(formatQuantity(2 / 3)).toBe('⅔')
    expect(formatQuantity(0.75)).toBe('¾')
    expect(formatQuantity(0.875)).toBe('⅞')
  })

  it('formats mixed numbers', () => {
    expect(formatQuantity(1.5)).toBe('1½')
    expect(formatQuantity(2.75)).toBe('2¾')
    expect(formatQuantity(14.25)).toBe('14¼')
  })

  it('snaps near-fraction decimals within tolerance', () => {
    expect(formatQuantity(0.1)).toBe('⅛')   // 0.1 ≈ 0.125, diff = 0.025 < 0.0625
    expect(formatQuantity(0.24)).toBe('¼')  // diff = 0.01 < 0.0625
    expect(formatQuantity(14.2)).toBe('14¼') // 0.2 ≈ 0.25, diff = 0.05 < 0.0625
  })

  it('snaps near-whole decimals to whole number', () => {
    expect(formatQuantity(1.97)).toBe('2')
    expect(formatQuantity(2.99)).toBe('3')
  })

  it('picks the nearest fraction when multiple are within tolerance', () => {
    // 0.26 is within tolerance of both ¼ (diff=0.01) and ⅓ (diff=0.073) → ¼ wins
    expect(formatQuantity(0.26)).toBe('¼')
    // 0.30 is within tolerance of both ¼ (diff=0.05) and ⅓ (diff=0.033) → ⅓ wins
    expect(formatQuantity(0.30)).toBe('⅓')
  })

  it('snaps near-zero decimal part to whole', () => {
    expect(formatQuantity(1.03)).toBe('1')   // 0.03 < TOLERANCE
    expect(formatQuantity(3.04)).toBe('3')
  })
})
