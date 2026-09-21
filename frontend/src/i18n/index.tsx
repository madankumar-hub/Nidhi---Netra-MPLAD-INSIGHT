import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { en } from './en'
import type { TranslationKey } from './en'
import { hi } from './hi'
import { translateEnum } from './enums'
import type { EnumFamily } from './enums'

export type Language = 'en' | 'hi'

const DICTIONARIES: Record<Language, Record<string, string>> = { en, hi }
const STORAGE_KEY = 'mplad.language'

export const LANGUAGES: { code: Language; label: string; nativeLabel: string }[] = [
  { code: 'en', label: 'English', nativeLabel: 'English' },
  { code: 'hi', label: 'Hindi', nativeLabel: 'हिन्दी' },
]

interface I18nContextValue {
  language: Language
  setLanguage: (language: Language) => void
  t: (key: TranslationKey, fallback?: string) => string
  /**
   * Translate a raw enum value that came from the API.
   *
   * The backend transmits English domain vocabulary; rendering it directly is
   * what used to leak English into Hindi mode. Every status, level, category
   * and role goes through here.
   */
  tEnum: (family: EnumFamily, value: string | null | undefined) => string
}

const I18nContext = createContext<I18nContextValue | null>(null)

function readStoredLanguage(): Language {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'en' || stored === 'hi') return stored
  } catch {
    /* storage unavailable */
  }
  return 'en'
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>(readStoredLanguage)

  useEffect(() => {
    document.documentElement.lang = language
    try {
      localStorage.setItem(STORAGE_KEY, language)
    } catch {
      /* ignore */
    }
  }, [language])

  const setLanguage = useCallback((next: Language) => setLanguageState(next), [])

  const t = useCallback(
    (key: TranslationKey, fallback?: string) => {
      const dictionary = DICTIONARIES[language]
      return dictionary[key] ?? en[key] ?? fallback ?? key
    },
    [language],
  )

  const tEnum = useCallback(
    (family: EnumFamily, enumValue: string | null | undefined) =>
      translateEnum(family, enumValue, language),
    [language],
  )

  const value = useMemo(
    () => ({ language, setLanguage, t, tEnum }),
    [language, setLanguage, t, tEnum],
  )
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useI18n(): I18nContextValue {
  const context = useContext(I18nContext)
  if (!context) throw new Error('useI18n must be used inside <I18nProvider>.')
  return context
}

export type { TranslationKey }
export type { EnumFamily }
