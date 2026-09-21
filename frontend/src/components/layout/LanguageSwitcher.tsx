import { Languages } from 'lucide-react'
import { LANGUAGES, useI18n } from '@/i18n'

/**
 * A segmented toggle rather than a <select>.
 *
 * The native dropdown inherits the control's background in Chromium on
 * Windows, so on the dark government bar the option list rendered dark text on
 * a dark surface and looked empty. Two buttons also make the bilingual support
 * visible at a glance instead of hiding it behind a click.
 */
export function LanguageSwitcher({ compact = false }: { compact?: boolean }) {
  const { language, setLanguage, t } = useI18n()

  return (
    <div className="flex items-center gap-2">
      <Languages className="h-4 w-4 shrink-0" aria-hidden />
      <span className={compact ? 'sr-only' : 'sr-only sm:not-sr-only'}>{t('nav.language')}</span>

      <div
        className="inline-flex rounded-md bg-white/10 p-0.5 ring-1 ring-inset ring-white/25"
        role="group"
        aria-label={t('nav.language')}
      >
        {LANGUAGES.map((option) => {
          const selected = option.code === language
          return (
            <button
              key={option.code}
              type="button"
              lang={option.code}
              aria-pressed={selected}
              onClick={() => setLanguage(option.code)}
              className={`rounded px-2.5 py-1 text-xs font-medium transition-colors ${
                selected
                  ? 'bg-white text-ink-900'
                  : 'text-white/80 hover:bg-white/15 hover:text-white'
              }`}
            >
              {option.nativeLabel}
            </button>
          )
        })}
      </div>
    </div>
  )
}
