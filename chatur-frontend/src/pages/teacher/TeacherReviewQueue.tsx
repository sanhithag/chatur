import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { CheckCircle, XCircle, Clock, ChevronDown, ChevronUp } from 'lucide-react'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { useI18n } from '@/i18n/I18nProvider'
import PageHeader from '@/components/PageHeader'
import LoadingSpinner from '@/components/LoadingSpinner'
import ErrorMessage from '@/components/ErrorMessage'

const PROPOSAL_COLORS: Record<string, string> = {
  down: 'border-l-amber-400 bg-amber-50',
  up: 'border-l-green-400 bg-green-50',
  revise: 'border-l-blue-400 bg-blue-50',
  reteach: 'border-l-purple-400 bg-purple-50',
}

export default function TeacherReviewQueue() {
  const { t } = useI18n()
  const user = useAuthStore((s) => s.user)
  const qc = useQueryClient()
  const [expanded, setExpanded] = useState<string | null>(null)
  const [notes, setNotes] = useState<Record<string, string>>({})

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['review-queue', user?.id],
    queryFn: async () => {
      const res = await api.get(`/teachers/${user?.id}/review-queue`)
      return res.data
    },
    enabled: !!user?.id,
  })

  const decideMutation = useMutation({
    mutationFn: async ({ proposalId, decision, teacherNotes }: { proposalId: string; decision: string; teacherNotes?: string }) => {
      await api.post(`/teachers/${user?.id}/review-queue/${proposalId}/decide`, {
        decision,
        teacher_notes: teacherNotes || null,
        time_spent_secs: 60,
      })
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['review-queue'] })
      qc.invalidateQueries({ queryKey: ['teacher-dashboard'] })
    },
  })

  if (isLoading) return <LoadingSpinner />
  if (isError) return <ErrorMessage onRetry={refetch} />

  const proposals: any[] = Array.isArray(data) ? data : (data?.proposals ?? [])

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <PageHeader
        title={t('nav_review')}
        subtitle={t('review_ai_advisory')}
        badge={proposals.length > 0 ? `${proposals.length} pending` : undefined}
      />

      {proposals.length === 0 ? (
        <div className="card p-8 text-center">
          <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
          <p className="text-slate-600 font-medium">{t('no_pending_proposals')}</p>
        </div>
      ) : (
        <div className="space-y-4">
          {proposals.map((p: any) => (
            <div key={p.id} className={`card border-l-4 ${PROPOSAL_COLORS[p.proposal_type] ?? 'border-l-slate-300'}`}>
              <div className="p-5">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-slate-900">{p.student_name}</span>
                      <span className={`badge ${
                        p.proposal_type === 'up' ? 'badge-green' :
                        p.proposal_type === 'down' ? 'badge-amber' :
                        'badge-blue'
                      }`}>
                        {t(`proposal_${p.proposal_type}` as any)}
                      </span>
                    </div>
                    <p className="text-sm text-slate-700 mb-2">
                      <span className="font-medium">{p.target_concept_name}</span>
                      {' → '}
                      <span className="font-medium text-accent-700">{p.proposed_level_name}</span>
                    </p>
                    <p className="text-sm text-slate-600">{p.narrative_en}</p>
                  </div>
                  <button
                    onClick={() => setExpanded(expanded === p.id ? null : p.id)}
                    className="text-slate-400 hover:text-slate-600 shrink-0 mt-1"
                  >
                    {expanded === p.id ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                  </button>
                </div>

                {/* Evidence (expandable) */}
                {expanded === p.id && (
                  <div className="mt-4 pt-4 border-t border-slate-200 space-y-3">
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{t('evidence_label')}</p>
                    {(p.evidence?.results ?? []).map((r: any, i: number) => (
                      <div key={i} className="flex items-center gap-3 text-sm">
                        <span className="text-slate-600 min-w-0 flex-1">{r.concept_name ?? r.concept_id}</span>
                        <span className={`font-medium ${r.score >= 0.67 ? 'text-green-600' : 'text-red-600'}`}>
                          {Math.round(r.score * 100)}%
                        </span>
                        {r.errors?.length > 0 && (
                          <span className="badge badge-red">{r.errors.join(', ')}</span>
                        )}
                      </div>
                    ))}
                    {/* Teacher notes */}
                    <textarea
                      className="input-field text-sm mt-2"
                      rows={2}
                      placeholder={t('teacher_notes_ph')}
                      value={notes[p.id] ?? ''}
                      onChange={(e) => setNotes({ ...notes, [p.id]: e.target.value })}
                    />
                  </div>
                )}

                {/* Action buttons */}
                <div className="flex gap-2 mt-4">
                  <button
                    className="btn-accent text-xs py-1.5"
                    disabled={decideMutation.isPending}
                    onClick={() => decideMutation.mutate({ proposalId: p.id, decision: 'approved', teacherNotes: notes[p.id] })}
                  >
                    <CheckCircle className="w-3.5 h-3.5" /> {t('approve')}
                  </button>
                  <button
                    className="btn-secondary text-xs py-1.5"
                    disabled={decideMutation.isPending}
                    onClick={() => decideMutation.mutate({ proposalId: p.id, decision: 'postponed', teacherNotes: notes[p.id] })}
                  >
                    <Clock className="w-3.5 h-3.5" /> {t('postpone')}
                  </button>
                  <button
                    className="btn-danger text-xs py-1.5"
                    disabled={decideMutation.isPending}
                    onClick={() => decideMutation.mutate({ proposalId: p.id, decision: 'rejected', teacherNotes: notes[p.id] })}
                  >
                    <XCircle className="w-3.5 h-3.5" /> {t('reject')}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
