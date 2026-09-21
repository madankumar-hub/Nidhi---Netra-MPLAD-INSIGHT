import { Link } from 'react-router-dom'
import { Compass } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { useI18n } from '@/i18n'

export function NotFoundPage() {
  const { t } = useI18n()
  return (
    <div className="mx-auto flex min-h-[60vh] max-w-lg flex-col items-center justify-center px-4 text-center">
      <Compass className="h-12 w-12 text-ink-400" aria-hidden />
      <h1 className="mt-4 text-2xl font-semibold text-ink-900">{t('notFound.title')}</h1>
      <p className="mt-2 text-sm text-ink-600">
        {t('notFound.body')}
      </p>
      <Link to="/" className="mt-6">
        <Button>{t('nav.home')}</Button>
      </Link>
    </div>
  )
}
