import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { LogOut, BookOpen, Globe } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useI18n } from '@/i18n/I18nProvider'
import type { Lang } from '@/i18n/translations'
import { formatLang } from '@/i18n/translations'

interface NavItem {
  to: string
  label: string
  icon: React.ReactNode
}

interface AppShellProps {
  navItems: NavItem[]
  roleLabel: string
  accentClass?: string
}

export default function AppShell({ navItems, roleLabel, accentClass = 'bg-primary-800' }: AppShellProps) {
  const { t, lang, setLang } = useI18n()
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const LANGS: Lang[] = ['en', 'te', 'hi']

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar */}
      <aside className={`w-64 ${accentClass} flex flex-col shrink-0`}>
        {/* Logo */}
        <div className="px-6 py-5 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-white/15 rounded-xl flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="text-white font-bold text-lg leading-none">{t('app_name')}</div>
              <div className="text-white/60 text-xs mt-0.5">{roleLabel}</div>
            </div>
          </div>
        </div>

        {/* Nav links */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-white/20 text-white'
                    : 'text-white/70 hover:bg-white/10 hover:text-white'
                }`
              }
            >
              {item.icon}
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* User info + language + logout */}
        <div className="px-3 py-4 border-t border-white/10 space-y-2">
          {/* Language switcher */}
          <div className="flex items-center gap-1.5 px-3 py-2">
            <Globe className="w-4 h-4 text-white/50 shrink-0" />
            <div className="flex gap-1 flex-wrap">
              {LANGS.map((l) => (
                <button
                  key={l}
                  onClick={() => setLang(l)}
                  className={`px-2 py-0.5 rounded text-xs font-medium transition-colors ${
                    lang === l ? 'bg-white text-primary-800' : 'text-white/70 hover:text-white'
                  }`}
                >
                  {formatLang(l)}
                </button>
              ))}
            </div>
          </div>

          {/* User */}
          <div className="px-3 py-2">
            <div className="text-white text-sm font-medium truncate">{user?.username}</div>
            <div className="text-white/50 text-xs capitalize">{user?.role?.replace('_', ' ')}</div>
          </div>

          {/* Logout */}
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 w-full px-3 py-2.5 rounded-lg text-white/70 hover:bg-white/10 hover:text-white text-sm font-medium transition-colors"
          >
            <LogOut className="w-4 h-4" />
            {t('sign_out')}
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
