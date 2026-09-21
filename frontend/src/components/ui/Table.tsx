import type { ReactNode } from 'react'

interface Column<T> {
  key: string
  header: ReactNode
  render: (row: T) => ReactNode
  /** Hidden below the `lg` breakpoint so tables stay readable on tablets. */
  secondary?: boolean
  align?: 'left' | 'right'
  width?: string
}

interface DataTableProps<T> {
  columns: Column<T>[]
  rows: T[]
  rowKey: (row: T) => string | number
  onRowClick?: (row: T) => void
  /** Card layout shown instead of the table on narrow screens. */
  renderCard?: (row: T) => ReactNode
  caption?: string
}

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  onRowClick,
  renderCard,
  caption,
}: DataTableProps<T>) {
  return (
    <>
      {renderCard ? (
        <ul className="space-y-3 md:hidden">
          {rows.map((row) => (
            <li key={rowKey(row)}>{renderCard(row)}</li>
          ))}
        </ul>
      ) : null}

      <div className={`overflow-x-auto ${renderCard ? 'hidden md:block' : ''}`}>
        <table className="w-full min-w-[640px] border-collapse text-sm">
          {caption ? <caption className="sr-only">{caption}</caption> : null}
          <thead>
            <tr className="border-b border-ink-200 bg-ink-50/70">
              {columns.map((column) => (
                <th
                  key={column.key}
                  scope="col"
                  style={column.width ? { width: column.width } : undefined}
                  className={`px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-ink-600
                    ${column.align === 'right' ? 'text-right' : 'text-left'}
                    ${column.secondary ? 'hidden lg:table-cell' : ''}`}
                >
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-100">
            {rows.map((row) => (
              <tr
                key={rowKey(row)}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                className={`bg-white transition-colors hover:bg-ink-50 ${
                  onRowClick ? 'cursor-pointer' : ''
                }`}
              >
                {columns.map((column) => (
                  <td
                    key={column.key}
                    className={`px-3 py-3 align-top text-ink-800
                      ${column.align === 'right' ? 'text-right tabular-nums' : ''}
                      ${column.secondary ? 'hidden lg:table-cell' : ''}`}
                  >
                    {column.render(row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}

export type { Column }
