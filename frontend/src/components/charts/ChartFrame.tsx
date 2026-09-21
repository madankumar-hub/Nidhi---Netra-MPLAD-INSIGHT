import type { ReactNode } from 'react'
import { BarChart3 } from 'lucide-react'
import { useI18n } from '@/i18n'

interface ChartFrameProps {
  title: string
  description?: string
  children: ReactNode
  /** When false the frame renders the empty state instead of the chart. */
  hasData: boolean
  emptyLabel: string
  height?: number
  actions?: ReactNode
  /** Optional accessible table alternative, shown in a <details>. */
  tableView?: ReactNode
  /**
   * Stretch to the height of the grid row. Only safe inside a grid that
   * actually defines one - as a plain stacked child, `h-full` resolves
   * against an auto-height parent and the figure can overflow its box.
   */
  fillRow?: boolean
}

export function ChartFrame({
  title,
  description,
  children,
  hasData,
  emptyLabel,
  height = 280,
  actions,
  tableView,
  fillRow = false,
}: ChartFrameProps) {
  const { t } = useI18n()
  return (
    <figure
      className={`surface flex min-w-0 flex-col p-4 sm:p-5 ${fillRow ? 'h-full' : ''}`}
    >
      <figcaption className="mb-3 flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-ink-900">{title}</h3>
          {description ? <p className="mt-0.5 text-xs text-ink-500">{description}</p> : null}
        </div>
        {actions}
      </figcaption>

      {hasData ? (
        <div style={{ height }} className="w-full">
          {children}
        </div>
      ) : (
        <div
          style={{ height }}
          className="flex w-full flex-col items-center justify-center gap-2 rounded-md border border-dashed border-ink-200 text-ink-400"
        >
          <BarChart3 className="h-6 w-6" aria-hidden />
          <p className="text-xs text-ink-500">{emptyLabel}</p>
        </div>
      )}

      {hasData && tableView ? (
        <details className="mt-3">
          <summary className="cursor-pointer text-xs font-medium text-ink-600 hover:text-ink-900">
            {t('chart.viewAsTable')}
          </summary>
          <div className="mt-2 max-h-56 overflow-auto">{tableView}</div>
        </details>
      ) : null}
    </figure>
  )
}

interface SimpleTableProps {
  head: string[]
  rows: (string | number)[][]
}

export function ChartTable({ head, rows }: SimpleTableProps) {
  return (
    <table className="w-full text-xs">
      <thead>
        <tr className="border-b border-ink-200 text-left text-ink-600">
          {head.map((cell) => (
            <th key={cell} scope="col" className="py-1.5 pr-3 font-medium">
              {cell}
            </th>
          ))}
        </tr>
      </thead>
      <tbody className="divide-y divide-ink-100">
        {rows.map((row, index) => (
          <tr key={index}>
            {row.map((cell, cellIndex) => (
              <td
                key={cellIndex}
                className={`py-1.5 pr-3 ${cellIndex === 0 ? 'text-ink-800' : 'tabular-nums text-ink-700'}`}
              >
                {cell}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
