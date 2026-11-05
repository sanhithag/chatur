import { useState, useEffect } from 'react'
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import {
  LogOut,
  Search,
  User,
  ChevronDown,
  BookOpen,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useI18n } from '@/i18n/I18nProvider'
import type { Lang } from '@/i18n/translations'
import { formatLang } from '@/i18n/translations'
import GlobalSearchModal from '@/components/GlobalSearchModal'

export interface NavItem {
  to: string
  label: string
  icon: React.ReactNode
  badge?: string | number
}

interface AppShellProps {
  navItems: NavItem[]
  roleLabel: string
  accentClass?: string
}

export default function AppShell({ navItems, roleLabel }: AppShellProps) {
  const { t, lang, setLang } = useI18n()
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()

  const [isSearchOpen, setIsSearchOpen] = useState(false)
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false)

  // Listen for keyboard shortcut Ctrl+K or Cmd+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        setIsSearchOpen((prev) => !prev)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const LANGS: Lang[] = ['en', 'te', 'hi']
  const profileLink = `/${user?.role === 'super_admin' ? 'admin' : user?.role || 'student'}/profile`

  return (
    <div className="min-h-screen bg-[#fefae0] flex flex-col font-sans text-[#000000]">
      {/* Top Header Bar: Clean, Ivory/Sand surface with Sage border */}
      <header className="h-14 bg-[#faedcd] border-b border-[#ccd5ae] flex items-center justify-between px-4 lg:px-6 sticky top-0 z-40 shrink-0 text-[#000000]">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(`/${user?.role === 'super_admin' ? 'admin' : user?.role || 'student'}`)}
            className="flex items-center gap-2 text-left group cursor-pointer"
          >
            <div className="w-8 h-8 rounded-md bg-[#ccd5ae] border border-[#ccd5ae] flex items-center justify-center text-[#000000]">
              <BookOpen className="w-4 h-4 text-[#000000]" />
            </div>
            <div>
              <div className="text-[#000000] font-bold text-lg tracking-tight leading-none">
                CHATUR
              </div>
              <div className="text-[#333333] text-[10px] font-medium uppercase tracking-wider mt-0.5">
                {roleLabel}
              </div>
            </div>
          </button>
        </div>

        {/* Global Search Bar (GeeksforGeeks inspired) */}
        <div className="flex-1 max-w-lg mx-4 lg:mx-8 hidden sm:block">
          <button
            type="button"
            onClick={() => setIsSearchOpen(true)}
            className="w-full flex items-center justify-between px-3.5 py-1.5 rounded-lg bg-white border border-[#ccd5ae] hover:border-[#d4a373] text-[#333333] transition-all cursor-pointer shadow-2xs"
          >
            <div className="flex items-center gap-2 text-xs">
              <Search className="w-3.5 h-3.5 text-[#333333]" />
              <span className="truncate">Search CBSE subjects, chapters, concepts, formulas…</span>
            </div>
            <kbd className="hidden md:inline-flex items-center px-1.5 py-0.5 text-[10px] font-mono rounded bg-[#faedcd] text-[#000000] border border-[#ccd5ae]">
              Ctrl K
            </kbd>
          </button>
        </div>

        {/* Right Menu: Language + User profile */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setIsSearchOpen(true)}
            className="sm:hidden p-1.5 rounded-lg bg-white border border-[#ccd5ae] text-[#000000]"
          >
            <Search className="w-4 h-4" />
          </button>

          {/* Language Selector: English, Telugu, Hindi */}
          <div className="flex items-center bg-white border border-[#ccd5ae] rounded-lg p-0.5 text-xs text-[#000000]">
            {LANGS.map((l) => (
              <button
                key={l}
                onClick={() => setLang(l)}
                className={`px-2 py-0.5 rounded-md font-medium transition-all cursor-pointer ${
                  lang === l
                    ? 'bg-[#ccd5ae] text-[#000000] font-bold shadow-2xs'
                    : 'text-[#333333] hover:bg-[#e9edc9]'
                }`}
              >
                {formatLang(l)}
              </button>
            ))}
          </div>

          {/* User Profile Dropdown */}
          <div className="relative">
            <button
              onClick={() => setIsProfileMenuOpen((prev) => !prev)}
              className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-white hover:bg-[#e9edc9] border border-[#ccd5ae] text-[#000000] transition-colors cursor-pointer"
            >
              <div className="w-6 h-6 rounded-full bg-[#d4a373] text-[#000000] font-bold text-xs flex items-center justify-center border border-[#ccd5ae]">
                {user?.username?.charAt(0).toUpperCase() || 'U'}
              </div>
              <span className="hidden md:inline text-xs font-medium text-[#000000] max-w-[120px] truncate">
                {user?.name || user?.username}
              </span>
              <ChevronDown className="w-3.5 h-3.5 text-[#333333]" />
            </button>

            {isProfileMenuOpen && (
              <div
                className="absolute right-0 mt-2 w-52 bg-white rounded-lg shadow-md border border-[#ccd5ae] py-1.5 z-50 text-[#000000]"
                onClick={() => setIsProfileMenuOpen(false)}
              >
                <div className="px-3.5 py-2 border-b border-[#ccd5ae]">
                  <p className="text-xs font-semibold text-[#000000] truncate">{user?.name || user?.username}</p>
                  <p className="text-[11px] text-[#333333] truncate">{user?.email || `@${user?.username}`}</p>
                  <span className="inline-block mt-1 text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-[#e9edc9] text-[#000000] border border-[#ccd5ae]">
                    {user?.role?.replace('_', ' ')}
                  </span>
                </div>

                <NavLink
                  to={profileLink}
                  className="flex items-center gap-2.5 px-3.5 py-2 text-xs font-medium text-[#000000] hover:bg-[#e9edc9]"
                >
                  <User className="w-3.5 h-3.5 text-[#333333]" />
                  {t('nav_profile')}
                </NavLink>

                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2.5 w-full text-left px-3.5 py-2 text-xs font-medium text-red-700 hover:bg-red-50 cursor-pointer"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  {t('sign_out')}
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Container: Sidebar + Content Canvas */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar Navigation */}
        <aside className="w-56 bg-[#e9edc9] border-r border-[#ccd5ae] flex flex-col shrink-0 text-[#000000]">
          <nav className="flex-1 px-2.5 py-3.5 space-y-1 overflow-y-auto">
            <div className="text-[10px] font-bold uppercase tracking-wider text-[#333333] px-2.5 mb-1.5">
              Menu
            </div>
            {navItems.map((item) => {
              const isActive = location.pathname === item.to || location.pathname.startsWith(item.to + '/')
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={`flex items-center justify-between px-3 py-2 rounded-md text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-[#ccd5ae] text-[#000000] font-bold border border-[#ccd5ae] shadow-2xs'
                      : 'text-[#000000] hover:bg-[#ccd5ae]/60'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <span className="text-[#000000]">{item.icon}</span>
                    <span>{item.label}</span>
                  </div>
                  {item.badge !== undefined && (
                    <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-[#d4a373] text-[#000000]">
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              )
            })}
          </nav>

          <div className="p-3 border-t border-[#ccd5ae] bg-[#faedcd]/40 text-xs text-[#333333]">
            <p className="font-semibold text-[#000000]">CBSE / NCERT</p>
            <p className="text-[11px] text-[#333333] mt-0.5">Classes 6 to 10 Curriculum</p>
          </div>
        </aside>

        {/* Workspace Canvas: Ivory background, comfortable typography */}
        <main className="flex-1 overflow-y-auto bg-[#fefae0] text-[#000000]">
          <Outlet />
        </main>
      </div>

      {/* Global Search Dialog Modal */}
      <GlobalSearchModal
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
      />
    </div>
  )
}
