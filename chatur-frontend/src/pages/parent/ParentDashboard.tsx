import { useQuery } from '@tanstack/react-query'
import { Heart, TrendingUp, BookOpen } from 'lucide-react'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { useI18n } from '@/i18n/I18nProvider'
import PageHeader from '@/components/PageHeader'
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

export default function ParentDashboard() {
  const { t } = useI18n()
  const user = useAuthStore((s) => s.user)

  // First get children list
  const childrenQuery = useQuery({
    queryKey: ['parent-children', user?.id],
    queryFn: async () => {
      const res = await api.get(`/parents/${user?.id}/children`)
      return res.data
    },
    enabled: !!user?.id,
  })

  const childrenData = childrenQuery.data
  const children: any[] = Array.isArray(childrenData)
    ? childrenData
    : (childrenData?.children ?? [])
  const firstChild = children[0]

  // Then get progress for first child
  const progressQuery = useQuery({
    queryKey: ['child-progress', user?.id, firstChild?.student_id],
    queryFn: async () => {
      const res = await api.get(`/parents/${user?.id}/children/${firstChild.student_id}/progress`)
      return res.data
    },
    enabled: !!user?.id && !!firstChild?.student_id,
  })

  if (childrenQuery.isLoading) return <LoadingSpinner />
  if (childrenQuery.isError) return <ErrorMessage onRetry={childrenQuery.refetch} />

  const progress = progressQuery.data
  const conceptProgress: any[] = progress?.concept_progress ?? progress?.concepts ?? []

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <PageHeader
        title={t('child_progress')}
        subtitle={t('weekly_tip')}
      />

      {children.length === 0 ? (
        <div className="card p-8 text-center">
          <Heart className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <p className="text-slate-500">{t('no_data')}</p>
        </div>
      ) : (
        <>
          {/* Child selector (if multiple children) */}
          {children.length > 1 && (
            <div className="flex gap-2 mb-6">
              {children.map((c: any) => (
                <div key={c.student_id} className="badge badge-blue px-3 py-1.5 text-sm">{c.student_name}</div>
              ))}
            </div>
          )}

          {/* Child card */}
          {firstChild && (
            <div className="card mb-6">
              <div className="card-header flex items-center gap-3">
                <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                  <BookOpen className="w-5 h-5 text-primary-700" />
                </div>
                <div>
                  <div className="font-semibold text-slate-900">{firstChild.student_name || firstChild.name}</div>
                  <div className="text-sm text-slate-500">Grade {firstChild.grade} · {firstChild.section}</div>
                </div>
                <div className="ml-auto text-right">
                  <div className="text-xl font-bold text-primary-800">{firstChild.total_xp}</div>
                  <div className="text-xs text-slate-500">{t('xp_points')}</div>
                </div>
              </div>
              <div className="card-body">
                <h3 className="text-sm font-semibold text-slate-700 mb-2">{t('weekly_tip')}</h3>
                <p className="text-sm text-slate-600 bg-amber-50 border border-amber-200 rounded-lg p-3">{t('weekly_tip_text')}</p>
              </div>
            </div>
          )}

          {/* Subject progress */}
          {progressQuery.isLoading ? (
            <LoadingSpinner />
          ) : (
            <div className="card">
              <div className="card-header flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-accent-600" />
                <h2 className="font-semibold text-slate-900">{t('subject_progress')}</h2>
              </div>
              <div className="card-body space-y-4">
                {conceptProgress.length === 0 ? (
                  <p className="text-sm text-slate-500">{t('no_data')}</p>
                ) : (
                  conceptProgress.map((cp: any) => (
                    <div key={cp.concept_id}>
                      <div className="flex justify-between mb-1">
                        <span className="text-sm font-medium text-slate-800">{cp.concept_name || cp.name}</span>
                        <span className={`text-xs font-medium ${(cp.on_track ?? cp.p_know >= 0.5) ? 'text-green-600' : 'text-amber-600'}`}>
                          {(cp.on_track ?? cp.p_know >= 0.5) ? `✅ ${t('on_track')}` : `🧭 ${t('needs_support')}`}
                        </span>
                      </div>
                      <MasteryBar value={cp.p_know} />
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
