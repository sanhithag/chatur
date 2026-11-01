import React, { createContext, useContext } from 'react'
import { useAuthStore } from '@/store/authStore'
import { t, type Lang } from '@/i18n/translations'

interface I18nContextValue {
  lang: Lang
  setLang: (lang: Lang) => void
  t: (key: string) => string
}

const I18nContext = createContext<I18nContextValue>({
  lang: 'en',
  setLang: () => {},
  t: (key) => key,
})

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const lang = useAuthStore((s) => s.lang)
  const setLang = useAuthStore((s) => s.setLang)

  const translate = React.useCallback(
    (key: string) => t(key, lang),
    [lang]
  )

  // Apply lang attribute to <html> for font-family switching
  React.useEffect(() => {
    document.documentElement.lang = lang
  }, [lang])

  return (
    <I18nContext.Provider value={{ lang, setLang, t: translate }}>
      {children}
    </I18nContext.Provider>
  )
}

export function useI18n() {
  return useContext(I18nContext)
}
