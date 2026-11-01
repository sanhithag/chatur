import { useQuery } from '@tanstack/react-query'
import { Flame, Star, BookOpen, TrendingUp, ChevronRight } from 'lucide-react'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { useI18n } from '@/i18n/I18nProvider'
import PageHeader from '@/components/PageHeader'
import StatCard from '@/components/StatCard'
import LoadingSpinner from '@/components/LoadingSpinner'
import ErrorMessage from '@/components/ErrorMessage'

function MasteryBar({ value }: { value: number }) {
  const pct = Math.round(value * 100)
  const color = value >= 0.8 ? 'bg-green-500' : value >= 0.5 ? 'bg-amber-400' : 'bg-red-400'
  return (
    <div className="flex items-center gap-2">
      <div className="mastery-bar flex-1">
        <div className={`mastery-fill ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-medium text-slate-600 w-8 text-right">{pct}%</span>
    </div>
  )
}

export default function StudentDashboard() {
  const { t } = useI18n()
  const user = useAuthStore((s) => s.user)

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['student-dashboard', user?.id],
    queryFn: async () => {
      const res = await api.get(`/students/${user?.id}/dashboard`)
      return res.data
    },
    enabled: !!user?.id,
  })

  if (isLoading) return <LoadingSpinner />
  if (isError) return <ErrorMessage onRetry={refetch} />

  const student = data?.student
  const mastery: Array<{ concept_id: string; concept_name: string; p_know: number; working_level_name?: string }> =
    data?.mastery_summary ?? []
  const subjects: Array<{ subject_name: string; concepts_in_progress: number }> = data?.enrolled_subjects ?? []

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <PageHeader
        title={`${t('welcome_back')}, ${student?.name ?? user?.username}!`}
        subtitle={t('today_plan')}
      />

      {/* Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
        <StatCard
          icon={<Star className="w-5 h-5 text-amber-500" />}
          label={t('xp_points')}
          value={student?.total_xp ?? 0}
          bg="bg-amber-50"
        />
        <StatCard
          icon={<Flame className="w-5 h-5 text-orange-500" />}
          label={t('streak_days')}
          value={student?.current_streak ?? 0}
          bg="bg-orange-50"
        />
        <StatCard
          icon={<BookOpen className="w-5 h-5 text-primary-600" />}
          label={t('my_subjects')}
          value={subjects.length}
          bg="bg-primary-50"
        />
        <StatCard
          icon={<TrendingUp className="w-5 h-5 text-green-600" />}
          label={t('concept_mastery')}
          value={mastery.length}
          bg="bg-green-50"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Concept Mastery panel */}
        <div className="lg:col-span-2 card">
          <div className="card-header flex items-center justify-between">
            <h2 className="text-base font-semibold text-slate-900">{t('concept_mastery')}</h2>
          </div>
          <div className="card-body space-y-4">
            {mastery.length === 0 ? (
              <p className="text-slate-500 text-sm">{t('no_data')}</p>
            ) : (
              mastery.map((m) => (
                <div key={m.concept_id} className="p-2.5 rounded-lg hover:bg-slate-50 transition-colors">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-sm font-medium text-slate-800">{m.concept_name}</span>
                    <div className="flex items-center gap-2">
                      {m.working_level_name && m.working_level_name !== m.concept_name && (
                        <span className="badge badge-blue text-xs">{t('foundation_path')}</span>
                      )}
                      <a
                        href={`/student/learn?concept_id=${m.concept_id}`}
                        className="text-xs px-2 py-0.5 rounded bg-primary-50 text-primary-700 hover:bg-primary-100 font-medium"
                      >
                        {t('nav_learn')}
                      </a>
                      <a
                        href={`/student/solve?concept_id=${m.concept_id}`}
                        className="text-xs px-2 py-0.5 rounded bg-amber-50 text-amber-700 hover:bg-amber-100 font-medium"
                      >
                        {t('nav_solve')}
                      </a>
                    </div>
                  </div>
                  <MasteryBar value={m.p_know} />
                </div>
              ))
            )}
          </div>
        </div>

        {/* Subjects panel */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-base font-semibold text-slate-900">{t('my_subjects')}</h2>
          </div>
          <div className="divide-y divide-slate-100">
            {subjects.length === 0 ? (
              <div className="p-4 text-sm text-slate-500">{t('no_data')}</div>
            ) : (
              subjects.map((s) => (
                <div key={s.subject_name} className="px-5 py-3 flex items-center justify-between hover:bg-slate-50 transition-colors">
                  <div>
                    <div className="text-sm font-medium text-slate-900">{s.subject_name}</div>
                    <div className="text-xs text-slate-500">{s.concepts_in_progress} concept(s) in progress</div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-400" />
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Privacy notice */}
      <p className="mt-6 text-xs text-slate-400 text-center">{t('level_private')}</p>
    </div>
  )
}
