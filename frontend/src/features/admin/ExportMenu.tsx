/**
 * Export the current selection as CSV or PDF (FR12).
 *
 * Two formats, two jobs: CSV goes into a spreadsheet for analysis, PDF is the
 * printable report an officer files or forwards. Rather than two buttons
 * competing for space, this is one button with a small menu.
 */
import { useEffect, useRef, useState } from 'react'
import { ChevronDown, Download, FileSpreadsheet, FileText } from 'lucide-react'
import { adminApi } from '@/api'
import type { ExportParams } from '@/api/admin'
import { useMutation } from '@/hooks/useApi'
import { useI18n } from '@/i18n'
import { Button } from '@/components/ui/Button'
import { InlineMessage } from '@/components/ui/States'

interface ExportMenuProps {
  params: ExportParams
}

export function ExportMenu({ params }: ExportMenuProps) {
  const { t } = useI18n()
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement | null>(null)

  const runExport = useMutation((format: 'csv' | 'pdf') => adminApi.exportProjects(params, format))

  // Close on an outside click or Escape, the way a menu is expected to behave.
  useEffect(() => {
    if (!open) return

    const onPointerDown = (event: MouseEvent) => {
      const node = containerRef.current
      if (node && !node.contains(event.target as Node)) setOpen(false)
    }
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false)
    }

    document.addEventListener('mousedown', onPointerDown)
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('mousedown', onPointerDown)
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [open])

  const choose = async (format: 'csv' | 'pdf') => {
    setOpen(false)
    await runExport.run(format)
  }

  const itemClass =
    'flex w-full items-start gap-2.5 px-3 py-2.5 text-left text-sm text-ink-800 hover:bg-ink-50'

  return (
    <div className="relative" ref={containerRef}>
      <Button
        variant="secondary"
        loading={runExport.pending}
        onClick={() => setOpen((value) => !value)}
        aria-haspopup="menu"
        aria-expanded={open}
        icon={<Download className="h-4 w-4" aria-hidden />}
      >
        {t('export.button')}
        <ChevronDown className="ml-1 h-3.5 w-3.5" aria-hidden />
      </Button>

      {open ? (
        <div
          role="menu"
          className="absolute right-0 z-20 mt-1 w-64 overflow-hidden rounded border border-ink-300 bg-white shadow-raised"
        >
          <button type="button" role="menuitem" className={itemClass} onClick={() => choose('csv')}>
            <FileSpreadsheet className="mt-0.5 h-4 w-4 shrink-0 text-ink-500" aria-hidden />
            <span>
              <span className="block font-medium">{t('export.csv')}</span>
              <span className="block text-xs text-ink-500">{t('export.csvHint')}</span>
            </span>
          </button>
          <button
            type="button"
            role="menuitem"
            className={`${itemClass} border-t border-ink-200`}
            onClick={() => choose('pdf')}
          >
            <FileText className="mt-0.5 h-4 w-4 shrink-0 text-ink-500" aria-hidden />
            <span>
              <span className="block font-medium">{t('export.pdf')}</span>
              <span className="block text-xs text-ink-500">{t('export.pdfHint')}</span>
            </span>
          </button>
        </div>
      ) : null}

      {runExport.error ? (
        <div className="absolute right-0 top-full z-20 mt-1 w-72">
          <InlineMessage tone="warning">{runExport.error.message}</InlineMessage>
        </div>
      ) : null}
    </div>
  )
}
