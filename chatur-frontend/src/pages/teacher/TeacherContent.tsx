import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { CheckCircle, XCircle, Sparkles } from 'lucide-react'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { useI18n } from '@/i18n/I18nProvider'
import PageHeader from '@/components/PageHeader'
import LoadingSpinner from '@/components/LoadingSpinner'
import ErrorMessage from '@/components/ErrorMessage'

export default function TeacherContent() {
  const { t } = useI18n()
  const user = useAuthStore((s) => s.user)
  const qc = useQueryClient()

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['content-queue', user?.id],
    queryFn: async () => {
      const res = await api.get(`/teachers/${user?.id}/content-queue`)
      return res.data
    },
    enabled: !!user?.id,
  })

  const decideMutation = useMutation({
    mutationFn: async ({ questionId, decision }: { questionId: string; decision: string }) => {
      await api.post(`/teachers/${user?.id}/content-queue/${questionId}/decide`, { decision, review_notes: null })
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['content-queue'] }),
  })

  if (isLoading) return <LoadingSpinner />
  if (isError) return <ErrorMessage onRetry={refetch} />

  const drafts: any[] = data?.drafts ?? []

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <PageHeader title={t('nav_content')} subtitle="AI-generated questions awaiting your review. Students cannot see these until approved." />

      {drafts.length === 0 ? (
        <div className="card p-8 text-center">
          <Sparkles className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <p className="text-slate-500">{t('no_data')}</p>
          <p className="text-sm text-slate-400 mt-1">AI draft questions will appear here for review.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {drafts.map((q: any) => (
            <div key={q.id} className="card">
              <div className="card-header flex items-center gap-2">
                <span className="badge badge-blue">{q.concept_name}</span>
                <span className={`badge ${q.difficulty === 'easy' ? 'badge-green' : q.difficulty === 'medium' ? 'badge-amber' : 'badge-red'}`}>
                  {q.difficulty}
                </span>
                <span className="badge badge-slate">{q.qtype}</span>
                <span className="ml-auto badge bg-purple-100 text-purple-800">
                  <Sparkles className="w-3 h-3" /> AI Draft
                </span>
              </div>
              <div className="card-body">
                <p className="text-slate-900 font-medium mb-3">{q.body_en?.text ?? q.body_en}</p>
                {q.answer_data?.options && (
                  <ol className="list-[upper-alpha] pl-5 space-y-1 text-sm text-slate-700 mb-4">
                    {q.answer_data.options.map((opt: string, i: number) => (
                      <li key={i} className={i === q.answer_data.correct_index ? 'font-semibold text-green-700' : ''}>
                        {opt} {i === q.answer_data.correct_index && '✓'}
                      </li>
                    ))}
                  </ol>
                )}
                <div className="flex gap-2">
                  <button
                    className="btn-accent text-xs py-1.5"
                    disabled={decideMutation.isPending}
                    onClick={() => decideMutation.mutate({ questionId: q.id, decision: 'approved' })}
                  >
                    <CheckCircle className="w-3.5 h-3.5" /> {t('approve')}
                  </button>
                  <button
                    className="btn-danger text-xs py-1.5"
                    disabled={decideMutation.isPending}
                    onClick={() => decideMutation.mutate({ questionId: q.id, decision: 'rejected' })}
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
