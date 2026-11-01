import { LayoutDashboard, Users, BookOpen, School, Activity } from 'lucide-react'
import AppShell from './AppShell'
import { useI18n } from '@/i18n/I18nProvider'
import { useAuthStore } from '@/store/authStore'

export default function AdminLayout() {
  const { t } = useI18n()
  const user = useAuthStore((s) => s.user)
  const isSuperAdmin = user?.role === 'super_admin'

  const navItems = [
    { to: '/admin/dashboard',  label: t('nav_dashboard'),   icon: <LayoutDashboard className="w-4 h-4" /> },
    { to: '/admin/users',      label: t('nav_users'),       icon: <Users className="w-4 h-4" /> },
    { to: '/admin/curriculum', label: t('nav_curriculum'),  icon: <BookOpen className="w-4 h-4" /> },
    { to: '/admin/impact',     label: t('nav_impact'),      icon: <Activity className="w-4 h-4" /> },
    ...(isSuperAdmin ? [{ to: '/admin/schools', label: t('nav_schools'), icon: <School className="w-4 h-4" /> }] : []),
  ]

  return (
    <AppShell
      roleLabel={t('role_admin')}
      accentClass="bg-violet-800"
      navItems={navItems}
    />
  )
}
