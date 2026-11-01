import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Users, AlertTriangle, ClipboardList, BookOpen, Check, X, Clock } from 'lucide-react'
import { useState } from 'react'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { useI18n } from '@/i18n/I18nProvider'
import PageHeader from '@/components/PageHeader'
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
    <div className="p-6 max-w-6xl mx-auto">
      <PageHeader title={t('class_overview')} subtitle={`${summary.section_name ?? ''} · ${summary.academic_year ?? ''}`} />

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
        <StatCard icon={<Users className="w-5 h-5 text-primary-600" />} label={t('total_students')} value={summary.total_students ?? 0} bg="bg-primary-50" />
        <StatCard icon={<ClipboardList className="w-5 h-5 text-amber-600" />} label={t('pending_reviews')} value={summary.pending_proposals ?? 0} bg="bg-amber-50" />
        <StatCard icon={<AlertTriangle className="w-5 h-5 text-red-500" />} label={t('concepts_with_gaps')} value={gapConcepts.length} bg="bg-red-50" />
        <StatCard icon={<BookOpen className="w-5 h-5 text-accent-600" />} label={t('students_attention')} value={attentionStudents.length} bg="bg-accent-50" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Concepts with widespread gaps */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-base font-semibold text-slate-900">{t('concepts_with_gaps')}</h2>
          </div>
          <div className="divide-y divide-slate-100">
            {gapConcepts.length === 0 ? (
              <div className="p-4 text-sm text-slate-500">{t('no_data')}</div>
            ) : (
              gapConcepts.map((c) => (
                <div key={c.concept_name} className="px-5 py-3 flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-800">{c.concept_name}</span>
                  <span className="badge badge-red">{c.student_count} students</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Students needing attention */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-base font-semibold text-slate-900">{t('students_attention')}</h2>
          </div>
          <div className="divide-y divide-slate-100">
            {attentionStudents.length === 0 ? (
              <div className="p-4 text-sm text-slate-500">{t('no_data')}</div>
            ) : (
              attentionStudents.map((s) => (
                <div key={s.student_name} className="px-5 py-3 flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-800">{s.student_name}</span>
                  <span className="badge badge-amber">{s.gap_count} gaps</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
