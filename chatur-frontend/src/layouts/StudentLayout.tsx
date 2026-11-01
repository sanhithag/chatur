import { LayoutDashboard, BookOpen, PenTool, FileText } from 'lucide-react'
import AppShell from './AppShell'
import { useI18n } from '@/i18n/I18nProvider'

export default function StudentLayout() {
  const { t } = useI18n()
  return (
    <AppShell
      roleLabel={t('role_student')}
      accentClass="bg-primary-800"
      navItems={[
        { to: '/student/dashboard', label: t('nav_dashboard'), icon: <LayoutDashboard className="w-4 h-4" /> },
        { to: '/student/learn',     label: t('nav_learn'),     icon: <BookOpen className="w-4 h-4" /> },
        { to: '/student/solve',     label: t('nav_solve'),     icon: <PenTool className="w-4 h-4" /> },
        { to: '/student/test',      label: t('nav_test'),      icon: <FileText className="w-4 h-4" /> },
      ]}
    />
  )
}
