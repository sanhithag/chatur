import { LayoutDashboard, TrendingUp } from 'lucide-react'
import AppShell from './AppShell'
import { useI18n } from '@/i18n/I18nProvider'

export default function ParentLayout() {
  const { t } = useI18n()
  return (
    <AppShell
      roleLabel={t('role_parent')}
      navItems={[
        { to: '/parent/dashboard', label: t('nav_dashboard'), icon: <LayoutDashboard className="w-4 h-4" /> },
        { to: '/parent/progress',  label: t('nav_progress'),  icon: <TrendingUp className="w-4 h-4" /> },
      ]}
    />
  )
}
