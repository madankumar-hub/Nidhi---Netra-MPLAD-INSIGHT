import { useEffect } from 'react'
import type { ReactNode } from 'react'
import { X } from 'lucide-react'
import { useI18n } from '@/i18n'

interface ModalProps {
  open: boolean
  title: string
  onClose: () => void
  children: ReactNode
  footer?: ReactNode
  size?: 'sm' | 'md' | 'lg'
}

const SIZES = { sm: 'max-w-md', md: 'max-w-xl', lg: 'max-w-3xl' }

export function Modal({ open, title, onClose, children, footer, size = 'md' }: ModalProps) {
  const { t } = useI18n()

  useEffect(() => {
    if (!open) return
    const handler = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-ink-950/40 p-0 sm:items-center sm:p-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={`flex max-h-[92vh] w-full flex-col rounded-t-xl bg-white shadow-raised sm:rounded-lg ${SIZES[size]}`}
      >
        <header className="flex items-center justify-between border-b border-ink-200 px-5 py-3">
          <h2 className="text-base font-semibold text-ink-900">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label={t('a11y.close')}
            className="tap-target -mr-2 flex items-center justify-center rounded-md text-ink-500 hover:bg-ink-100 hover:text-ink-800"
          >
            <X className="h-5 w-5" aria-hidden />
          </button>
        </header>
        <div className="flex-1 overflow-y-auto px-5 py-4">{children}</div>
        {footer ? (
          <footer className="flex justify-end gap-2 border-t border-ink-200 px-5 py-3">{footer}</footer>
        ) : null}
      </div>
    </div>
  )
}