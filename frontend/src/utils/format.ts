/** Formatting helpers. MPLAD amounts are held in rupees lakh. */

export function formatLakh(value?: number | null, options: { compact?: boolean } = {}): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  if (options.compact && value >= 100) {
    return `₹${(value / 100).toLocaleString('en-IN', { maximumFractionDigits: 2 })} Cr`
  }
  return `₹${value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} L`
}

export function formatNumber(value?: number | null): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return value.toLocaleString('en-IN')
}

export function formatPercent(value?: number | null, digits = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return `${value.toFixed(digits)}%`
}

export function formatDate(value?: string | null): string {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

export function formatDateTime(value?: string | null): string {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function relativeDays(value?: string | null): string {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  const diff = Math.round((Date.now() - date.getTime()) / 86_400_000)
  if (diff === 0) return 'today'
  if (diff === 1) return 'yesterday'
  if (diff < 30) return `${diff} days ago`
  if (diff < 365) return `${Math.round(diff / 30)} months ago`
  return `${Math.round(diff / 365)} years ago`
}

export function formatPeriod(period: string): string {
  // "2025-07" -> "Jul 2025"
  const match = /^(\d{4})-(\d{2})$/.exec(period)
  if (!match) return period
  const date = new Date(Number(match[1]), Number(match[2]) - 1, 1)
  return date.toLocaleDateString('en-IN', { month: 'short', year: 'numeric' })
}

export function truncate(text: string, length = 120): string {
  if (text.length <= length) return text
  return `${text.slice(0, length - 1).trimEnd()}…`
}

export function todayIso(): string {
  return new Date().toISOString().slice(0, 10)
}
