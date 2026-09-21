/**
 * The utility strip that sits above the masthead on Indian government portals.
 *
 * GIGW 3.0 requires a government website to let the visitor change text size
 * and switch to a high-contrast view without installing anything, and to offer
 * a skip link to the main content. Those controls live here.
 *
 * Preferences are per-visitor conveniences, so localStorage is the right home
 * for them - but it throws in a private window and can return stale or empty
 * values, so every access is guarded and the UI renders correctly without it.
 */
import { useCallback, useEffect, useState } from 'react'
import { Contrast, Minus, Plus, Type } from 'lucide-react'
import { useI18n } from '@/i18n'
import { LanguageSwitcher } from './LanguageSwitcher'

const SCALE_KEY = 'mplad.textScale'
const CONTRAST_KEY = 'mplad.contrast'

/** 100%, 112.5%, 125% - three steps is the GIGW convention. */
const SCALES = [1, 1.125, 1.25] as const
const DEFAULT_SCALE_INDEX = 0

function readStoredScaleIndex(): number {
  try {
    const stored = Number(localStorage.getItem(SCALE_KEY))
    if (Number.isInteger(stored) && stored >= 0 && stored < SCALES.length) return stored
  } catch {
    /* storage unavailable - fall through to the default */
  }
  return DEFAULT_SCALE_INDEX
}

function readStoredContrast(): boolean {
  try {
    return localStorage.getItem(CONTRAST_KEY) === 'high'
  } catch {
    return false
  }
}

export function AccessibilityBar() {
  const { t } = useI18n()
  const [scaleIndex, setScaleIndex] = useState(readStoredScaleIndex)
  const [highContrast, setHighContrast] = useState(readStoredContrast)

  useEffect(() => {
    document.documentElement.style.setProperty('--text-scale', String(SCALES[scaleIndex]))
    try {
      localStorage.setItem(SCALE_KEY, String(scaleIndex))
    } catch {
      /* ignore */
    }
  }, [scaleIndex])

  useEffect(() => {
    if (highContrast) {
      document.documentElement.setAttribute('data-contrast', 'high')
    } else {
      document.documentElement.removeAttribute('data-contrast')
    }
    try {
      localStorage.setItem(CONTRAST_KEY, highContrast ? 'high' : 'normal')
    } catch {
      /* ignore */
    }
  }, [highContrast])

  const decrease = useCallback(() => setScaleIndex((i) => Math.max(0, i - 1)), [])
  const reset = useCallback(() => setScaleIndex(DEFAULT_SCALE_INDEX), [])
  const increase = useCallback(
    () => setScaleIndex((i) => Math.min(SCALES.length - 1, i + 1)),
    [],
  )

  const buttonClass =
    'inline-flex h-7 items-center gap-1 rounded border border-white/25 px-2 text-xs ' +
    'font-medium text-white/90 transition-colors hover:border-white/50 hover:bg-white/10 ' +
    'disabled:cursor-not-allowed disabled:border-white/10 disabled:text-white/40'

  return (
    <div className="no-print bg-ink-950 text-white">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-4 gap-y-1 px-4 py-1.5">
        <p className="text-xs font-medium text-white/90">{t('gov.bar')}</p>

        <div className="ml-auto flex items-center gap-2">
          {/* Text size */}
          <div
            className="flex items-center gap-1"
            role="group"
            aria-label={t('a11y.textSize')}
          >
            <Type className="h-3.5 w-3.5 text-white/60" aria-hidden />
            <button
              type="button"
              onClick={decrease}
              disabled={scaleIndex === 0}
              className={buttonClass}
              aria-label={t('a11y.decreaseText')}
            >
              <Minus className="h-3 w-3" aria-hidden />
            </button>
            <button
              type="button"
              onClick={reset}
              className={buttonClass}
              aria-label={t('a11y.resetText')}
            >
              A
            </button>
            <button
              type="button"
              onClick={increase}
              disabled={scaleIndex === SCALES.length - 1}
              className={buttonClass}
              aria-label={t('a11y.increaseText')}
            >
              <Plus className="h-3 w-3" aria-hidden />
            </button>
          </div>

          {/* High contrast */}
          <button
            type="button"
            onClick={() => setHighContrast((value) => !value)}
            aria-pressed={highContrast}
            className={buttonClass}
          >
            <Contrast className="h-3.5 w-3.5" aria-hidden />
            <span className="hidden sm:inline">{t('a11y.contrast')}</span>
          </button>

          <LanguageSwitcher />
        </div>
      </div>
    </div>
  )
}
