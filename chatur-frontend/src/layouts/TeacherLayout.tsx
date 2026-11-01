import { LayoutDashboard, Grid3x3, ClipboardList, Users, BookCheck, Activity } from 'lucide-react'
import AppShell from './AppShell'
import { useI18n } from '@/i18n/I18nProvider'

export default function TeacherLayout() {
  const { t } = useI18n()
  return (
    <AppShell
      roleLabel={t('role_teacher')}
      accentClass="bg-accent-700"
      navItems={[
        { to: '/teacher/dashboard', label: t('nav_dashboard'),  icon: <LayoutDashboard className="w-4 h-4" /> },
        { to: '/teacher/heatmap',   label: t('nav_heatmap'),    icon: <Grid3x3 className="w-4 h-4" /> },
        { to: '/teacher/review',    label: t('nav_review'),     icon: <ClipboardList className="w-4 h-4" /> },
        { to: '/teacher/groups',    label: t('nav_groups'),     icon: <Users className="w-4 h-4" /> },
        { to: '/teacher/content',   label: t('nav_content'),    icon: <BookCheck className="w-4 h-4" /> },
        { to: '/teacher/impact',    label: t('nav_impact'),     icon: <Activity className="w-4 h-4" /> },
      ]}
    />
  )
}
