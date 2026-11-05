import { LayoutDashboard, BookOpen, Target, FileCheck, BarChart3, CheckSquare, User } from 'lucide-react'
import AppShell from './AppShell'
import { useI18n } from '@/i18n/I18nProvider'

export default function StudentLayout() {
  const { t } = useI18n()
  return (
    <AppShell
      roleLabel={t('role_student')}
      navItems={[
        { to: '/student/dashboard', label: t('nav_home'), icon: <LayoutDashboard className="w-4 h-4" /> },
        { to: '/student/learn', label: t('nav_learn'), icon: <BookOpen className="w-4 h-4" /> },
        { to: '/student/practice', label: t('nav_practice'), icon: <Target className="w-4 h-4" /> },
        { to: '/student/test', label: t('nav_weekly_tests'), icon: <FileCheck className="w-4 h-4" /> },
        { to: '/student/progress', label: t('nav_my_progress'), icon: <BarChart3 className="w-4 h-4" /> },
        { to: '/student/tasks', label: t('nav_todo'), icon: <CheckSquare className="w-4 h-4" /> },
        { to: '/student/profile', label: t('nav_profile'), icon: <User className="w-4 h-4" /> },
      ]}
    />
  )
}
