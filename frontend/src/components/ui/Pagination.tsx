import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useI18n } from '@/i18n'
import { Button } from './Button'

interface PaginationProps {
  page: number
  totalPages: number
  total: number
  pageSize: number
  onChange: (page: number) => void
  labels: { previous: string; next: string; showing: string; results: string; page: string; of: string }
}

export function Pagination({
  page,
  totalPages,
  total,
  pageSize,
  onChange,
  labels,
}: PaginationProps) {
  const { t } = useI18n()
  if (total === 0) return null
  const first = (page - 1) * pageSize + 1
  const last = Math.min(page * pageSize, total)

  return (
    <nav
      className="flex flex-col items-center justify-between gap-3 border-t border-ink-200 px-1 pt-4 sm:flex-row"
      aria-label={t('a11y.pagination')}
    >
      <p className="text-sm text-ink-600">
        {labels.showing} <span className="font-medium text-ink-900">{first}</span>–
        <span className="font-medium text-ink-900">{last}</span> {labels.of}{' '}
        <span className="font-medium text-ink-900">{total.toLocaleString('en-IN')}</span>{' '}
        {labels.results}
      </p>
      <div className="flex items-center gap-2">
        <Button
          variant="secondary"
          size="sm"
          className="tap-target"
          disabled={page <= 1}
          onClick={() => onChange(page - 1)}
          icon={<ChevronLeft className="h-4 w-4" aria-hidden />}
        >
          {labels.previous}
        </Button>
        <span className="px-2 text-sm text-ink-700">
          {labels.page} {page} {labels.of} {totalPages}
        </span>
        <Button
          variant="secondary"
          size="sm"
          className="tap-target"
          disabled={page >= totalPages}
          onClick={() => onChange(page + 1)}
        >
          {labels.next}
          <ChevronRight className="h-4 w-4" aria-hidden />
        </Button>
      </div>
    </nav>
  )
}
