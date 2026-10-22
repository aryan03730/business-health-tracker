const money = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 2,
  minimumFractionDigits: 0,
})
const number = new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 })

export const formatMoney = (n) => money.format(n)
export const formatNumber = (n) => number.format(n)

/** "12,500.5" -> "12500.5"; leaves anything else for validation to reject */
export const cleanNumber = (s) => String(s ?? '').replace(/[,$\s]/g, '')
