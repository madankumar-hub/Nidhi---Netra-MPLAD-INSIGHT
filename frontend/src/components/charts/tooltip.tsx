import type { ReactNode } from 'react'

export interface TooltipEntry {
  name?: string | number
  value?: number | string
  color?: string
  dataKey?: string | number
}

interface ChartTooltipProps {
  active?: boolean
  label?: ReactNode
  payload?: TooltipEntry[]
  formatter?: (value: number, key: string) => string
  labelFormatter?: (label: ReactNode) => ReactNode
}

/**
 * Shared tooltip. Values stay in ink colours; the coloured swatch beside the
 * label carries series identity (text never wears the series colour).
 */
export function ChartTooltip({
  active,
  label,
  payload,
  formatter,
  labelFormatter,
}: ChartTooltipProps) {
  if (!active || !payload || payload.length === 0) return null
  return (
    <div className="rounded-lg border border-ink-200 bg-white px-3 py-2 text-xs shadow-raised">
      {label !== undefined && label !== null ? (
        <p className="mb-1.5 font-semibold text-ink-900">
          {labelFormatter ? labelFormatter(label) : label}
        </p>
      ) : null}
      <ul className="space-y-1">
        {payload.map((entry, index) => (
          <li key={index} className="flex items-center justify-between gap-4">
            <span className="flex items-center gap-1.5 text-ink-600">
              <span
                className="h-2 w-2 shrink-0 rounded-sm"
                style={{ backgroundColor: entry.color }}
                aria-hidden
              />
              {entry.name}
            </span>
            <span className="font-medium tabular-nums text-ink-900">
              {typeof entry.value === 'number' && formatter
                ? formatter(entry.value, String(entry.dataKey ?? ''))
                : entry.value}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
