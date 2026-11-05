import { useQuery } from '@tanstack/react-query'
import { Users, AlertTriangle, ClipboardList, BookOpen } from 'lucide-react'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { useI18n } from '@/i18n/I18nProvider'
import StatCard from '@/components/StatCard'
import LoadingSpinner from '@/components/LoadingSpinner'
import ErrorMessage from '@/components/ErrorMessage'

export default function TeacherDashboard() {
  const { t } = useI18n()
  const user = useAuthStore((s) => s.user)

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['teacher-dashboard', user?.id],
    queryFn: async () => {
      const res = await api.get(`/teachers/${user?.id}/dashboard`)
      return res.data
    },
    enabled: !!user?.id,
  })

  if (isLoading) return <LoadingSpinner />
  if (isError) return <ErrorMessage onRetry={refetch} />

  const summary = data?.summary ?? {}
  const gapConcepts: Array<{ concept_name: string; student_count: number }> = data?.concepts_with_gaps ?? []
  const attentionStudents: Array<{ student_name: string; gap_count: number }> = data?.students_needing_attention ?? []

  return (
    <div className="p-4 lg:p-8 max-w-6xl mx-auto space-y-6">
      <div className="border-b border-[#ccd5ae] pb-4">
        <h1 className="text-2xl font-black text-[#000000] flex items-center gap-2">
          <BookOpen className="w-6 h-6 text-[#000000]" />
          Class Overview
        </h1>
        <p className="text-xs sm:text-sm text-[#333333] mt-1">
          {summary.section_name ?? 'Class 9-A'} • {summary.academic_year ?? '2025-2026'}
        </p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard icon={<Users className="w-5 h-5 text-[#000000]" />} label={t('total_students')} value={summary.total_students ?? 0} />
        <StatCard icon={<ClipboardList className="w-5 h-5 text-[#000000]" />} label={t('pending_reviews')} value={summary.pending_proposals ?? 0} />
        <StatCard icon={<AlertTriangle className="w-5 h-5 text-[#000000]" />} label={t('concepts_with_gaps')} value={gapConcepts.length} />
        <StatCard icon={<BookOpen className="w-5 h-5 text-[#000000]" />} label={t('students_attention')} value={attentionStudents.length} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Concepts with widespread gaps */}
        <div className="card bg-white border border-[#ccd5ae]">
          <div className="card-header bg-[#faedcd]/40 border-b border-[#ccd5ae] p-4">
            <h2 className="text-base font-bold text-[#000000]">{t('concepts_with_gaps')}</h2>
          </div>
          <div className="divide-y divide-[#ccd5ae]">
            {gapConcepts.length === 0 ? (
              <div className="p-4 text-xs text-[#333333]">{t('no_data')}</div>
            ) : (
              gapConcepts.map((c) => (
                <div key={c.concept_name} className="px-5 py-3 flex items-center justify-between">
                  <span className="text-xs font-bold text-[#000000]">{c.concept_name}</span>
                  <span className="text-xs font-bold px-2 py-0.5 rounded bg-[#faedcd] text-[#000000] border border-[#ccd5ae]">
                    {c.student_count} students
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Students needing attention */}
        <div className="card bg-white border border-[#ccd5ae]">
          <div className="card-header bg-[#faedcd]/40 border-b border-[#ccd5ae] p-4">
            <h2 className="text-base font-bold text-[#000000]">{t('students_attention')}</h2>
          </div>
          <div className="divide-y divide-[#ccd5ae]">
            {attentionStudents.length === 0 ? (
              <div className="p-4 text-xs text-[#333333]">{t('no_data')}</div>
            ) : (
              attentionStudents.map((s) => (
                <div key={s.student_name} className="px-5 py-3 flex items-center justify-between">
                  <span className="text-xs font-bold text-[#000000]">{s.student_name}</span>
                  <span className="text-xs font-bold px-2 py-0.5 rounded bg-[#e9edc9] text-[#000000] border border-[#ccd5ae]">
                    {s.gap_count} gaps
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
