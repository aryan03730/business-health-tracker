// Mirrors backend/calculations.py validate_inputs so users get instant feedback.
// The server still validates everything; its messages win if they differ.
import { cleanNumber } from './format.js'

// Must match NUMBER_PATTERN in backend/calculations.py
export const NUMBER_PATTERN = /^-?(\d+\.?\d*|\.\d+)$/

export const FIELDS = {
  initial_investment: 'Initial investment',
  monthly_running_costs: 'Monthly running costs',
  selling_price: 'Selling price per unit',
  cost_per_unit: 'Cost per unit',
  units_sold: 'Units sold this month',
}

export const STEP_FIELDS = [
  ['name', 'initial_investment', 'monthly_running_costs'],
  ['selling_price', 'cost_per_unit'],
  ['units_sold'],
]

function parse(raw, label) {
  const s = cleanNumber(raw)
  if (s === '') return { error: `${label} is required.` }
  if (!NUMBER_PATTERN.test(s)) return { error: `${label} must be a number.` }
  const n = Number(s)
  if (n > 1e12) return { error: `${label} is too large.` }
  return { value: n }
}

export function validate(values, fields = Object.keys(FIELDS)) {
  const errors = {}
  const nums = {}
  for (const f of fields) {
    if (!(f in FIELDS)) continue
    const { value, error } = parse(values[f], FIELDS[f])
    if (error) errors[f] = error
    else nums[f] = value
  }
  const rule = (f, ok, msg) => {
    if (f in nums && !errors[f] && !ok(nums[f])) errors[f] = msg
  }
  rule('initial_investment', (v) => v >= 0, 'Initial investment cannot be negative.')
  rule('monthly_running_costs', (v) => v >= 0, 'Monthly running costs cannot be negative.')
  rule('selling_price', (v) => v > 0, 'Selling price must be greater than zero.')
  rule('cost_per_unit', (v) => v >= 0, 'Cost per unit cannot be negative.')
  rule('units_sold', (v) => v >= 0, 'Units sold cannot be negative.')
  rule('units_sold', (v) => Number.isInteger(v), 'Units sold must be a whole number.')

  if (
    'selling_price' in nums && 'cost_per_unit' in nums &&
    !errors.selling_price && !errors.cost_per_unit &&
    nums.selling_price <= nums.cost_per_unit
  ) {
    errors.selling_price =
      'Selling price must be higher than the cost per unit, otherwise every sale loses money and break-even is not possible.'
  }
  if (fields.includes('name') && (values.name || '').trim().length > 120) {
    errors.name = 'Name must be 120 characters or fewer.'
  }
  return errors
}

export function toPayload(values) {
  const out = { name: (values.name || '').trim() }
  for (const f of Object.keys(FIELDS)) out[f] = Number(cleanNumber(values[f]))
  return out
}
