import { useQuery } from '@tanstack/react-query'
import { School, Users, BookOpen, Activity, CheckCircle, Clock, AlertCircle } from 'lucide-react'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { useI18n } from '@/i18n/I18nProvider'
import PageHeader from '@/components/PageHeader'
import StatCard from '@/components/StatCard'
import LoadingSpinner from '@/components/LoadingSpinner'
import ErrorMessage from '@/components/ErrorMessage'

export default function AdminDashboard() {
  const { t } = useI18n()
  const user = useAuthStore((s) => s.user)

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['admin-overview', user?.school_id],
    queryFn: async () => {
      const res = await api.get(`/admin/curriculum/overview`)
      return res.data
    },
  })

  if (isLoading) return <LoadingSpinner />
  if (isError) return <ErrorMessage onRetry={refetch} />

  const overview = data ?? {}
  const subjects: any[] = overview.subjects ?? []

  const totalConcepts = subjects.reduce((s: number, sub: any) => s + (sub.total_concepts ?? 0), 0)
  const adaptiveReady = subjects.reduce((s: number, sub: any) => s + (sub.adaptive_ready ?? 0), 0)
  const awaiting = totalConcepts - adaptiveReady

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <PageHeader title={t('admin_dashboard')} subtitle={overview.school_name ?? ''} />

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
        <StatCard icon={<BookOpen className="w-5 h-5 text-primary-600" />} label={t('total_concepts')} value={totalConcepts} bg="bg-primary-50" />
        <StatCard icon={<CheckCircle className="w-5 h-5 text-green-600" />} label={t('adaptive_ready')} value={adaptiveReady} bg="bg-green-50" />
        <StatCard icon={<Clock className="w-5 h-5 text-amber-600" />} label={t('awaiting_content')} value={awaiting} bg="bg-amber-50" />
        <StatCard icon={<Activity className="w-5 h-5 text-accent-600" />} label="Total Subjects" value={subjects.length} bg="bg-accent-50" />
      </div>

      {/* Curriculum coverage table */}
      <div className="card">
        <div className="card-header flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-primary-700" />
          <h2 className="font-semibold text-slate-900">{t('curriculum_coverage')}</h2>
          <span className="ml-auto text-xs text-slate-500">CBSE 2026-27</span>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                <th className="px-4 py-3 text-left font-medium text-slate-700">Subject</th>
                <th className="px-4 py-3 text-center font-medium text-slate-700">Total Concepts</th>
                <th className="px-4 py-3 text-center font-medium text-slate-700">Adaptive Ready</th>
                <th className="px-4 py-3 text-center font-medium text-slate-700">Draft</th>
                <th className="px-4 py-3 text-center font-medium text-slate-700">Awaiting</th>
                <th className="px-4 py-3 text-center font-medium text-slate-700">Coverage</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {subjects.map((sub: any) => {
                const pct = sub.total_concepts ? Math.round((sub.adaptive_ready / sub.total_concepts) * 100) : 0
                return (
                  <tr key={sub.subject_code} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-medium text-slate-900">{sub.subject_name}</td>
                    <td className="px-4 py-3 text-center text-slate-700">{sub.total_concepts}</td>
                    <td className="px-4 py-3 text-center">
                      <span className="badge badge-green">{sub.adaptive_ready}</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="badge badge-amber">{sub.draft ?? 0}</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="badge badge-red">{sub.awaiting_content ?? 0}</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex items-center gap-2 justify-center">
                        <div className="w-16 bg-slate-200 rounded-full h-2">
                          <div className="bg-green-500 h-2 rounded-full" style={{ width: `${pct}%` }} />
                        </div>
                        <span className="text-xs text-slate-600">{pct}%</span>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        <div className="px-4 py-3 bg-amber-50 border-t border-amber-100 text-xs text-amber-700 flex items-start gap-2">
          <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
          Content coverage is a real-time measure. A concept is "Adaptive Ready" only when it has ≥3 approved questions and an approved lesson. Figures reflect actual data, not projections.
        </div>
      </div>
    </div>
  )
}
