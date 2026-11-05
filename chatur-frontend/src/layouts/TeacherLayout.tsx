import { LayoutDashboard, BookOpen, Target, FileCheck, Grid3x3, ClipboardList, Users, BookCheck, User } from 'lucide-react'
import AppShell from './AppShell'
import { useI18n } from '@/i18n/I18nProvider'

export default function TeacherLayout() {
  const { t } = useI18n()
  return (
    <AppShell
      roleLabel={t('role_teacher')}
      navItems={[
        { to: '/teacher/dashboard', label: t('nav_dashboard'), icon: <LayoutDashboard className="w-4 h-4" /> },
        { to: '/teacher/learn', label: t('nav_learn'), icon: <BookOpen className="w-4 h-4" /> },
        { to: '/teacher/practice', label: t('nav_practice'), icon: <Target className="w-4 h-4" /> },
        { to: '/teacher/test', label: t('nav_weekly_tests'), icon: <FileCheck className="w-4 h-4" /> },
        { to: '/teacher/heatmap', label: t('nav_heatmap'), icon: <Grid3x3 className="w-4 h-4" /> },
        { to: '/teacher/review', label: t('nav_review'), icon: <ClipboardList className="w-4 h-4" /> },
        { to: '/teacher/groups', label: t('nav_groups'), icon: <Users className="w-4 h-4" /> },
        { to: '/teacher/content', label: t('nav_content'), icon: <BookCheck className="w-4 h-4" /> },
        { to: '/teacher/profile', label: t('nav_profile'), icon: <User className="w-4 h-4" /> },
      ]}
    />
  )
}
