import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Lang } from '@/i18n/translations'

export interface AuthUser {
  id: string
  username: string
  role: 'student' | 'teacher' | 'parent' | 'admin' | 'super_admin'
  preferred_lang: Lang
  school_id: string | null
  display_name?: string
}

interface AuthState {
  user: AuthUser | null
  accessToken: string | null
  refreshToken: string | null
  lang: Lang
  setAuth: (user: AuthUser, accessToken: string, refreshToken: string) => void
  setTokens: (accessToken: string, refreshToken: string) => void
  setLang: (lang: Lang) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      lang: 'en',
      setAuth: (user, accessToken, refreshToken) =>
        set({ user, accessToken, refreshToken, lang: user.preferred_lang }),
      setTokens: (accessToken, refreshToken) =>
        set({ accessToken, refreshToken }),
      setLang: (lang) => set({ lang }),
      logout: () => set({ user: null, accessToken: null, refreshToken: null }),
    }),
    { name: 'chatur-auth' }
  )
)
