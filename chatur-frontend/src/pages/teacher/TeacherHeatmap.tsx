import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { useI18n } from '@/i18n/I18nProvider'
import PageHeader from '@/components/PageHeader'
import LoadingSpinner from '@/components/LoadingSpinner'
import ErrorMessage from '@/components/ErrorMessage'

function masteryColor(v: number | null): string {
  if (v === null || v === undefined) return 'bg-slate-100 text-slate-400'
  if (v >= 0.8) return 'bg-green-100 text-green-800'
  if (v >= 0.5) return 'bg-amber-100 text-amber-800'
  return 'bg-red-100 text-red-800'
}

export default function TeacherHeatmap() {
  const { t } = useI18n()
  const user = useAuthStore((s) => s.user)

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['heatmap', user?.id],
    queryFn: async () => {
      const res = await api.get(`/teachers/${user?.id}/heatmap`)
      return res.data
    },
    enabled: !!user?.id,
  })

  if (isLoading) return <LoadingSpinner />
  if (isError) return <ErrorMessage onRetry={refetch} />

  const students: any[] = data?.students ?? (Array.isArray(data) ? data : [])
  const concepts: any[] = data?.concepts ?? []

  return (
    <div className="p-6 max-w-full">
      <PageHeader title={t('heatmap_title')} subtitle="Concept mastery across all students in your class" />

      <div className="card overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200">
              <th className="px-4 py-3 text-left font-medium text-slate-700 sticky left-0 bg-slate-50">Student</th>
              {concepts.map((c: any) => (
                <th key={c.id} className="px-3 py-3 text-center font-medium text-slate-600 min-w-[100px]">
                  <div className="text-xs leading-tight">
                    {c.name_en}
                    <div className="text-slate-400 font-normal">Gr {c.grade}</div>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {students.length === 0 ? (
              <tr><td colSpan={concepts.length + 1} className="px-4 py-8 text-center text-slate-500">{t('no_data')}</td></tr>
            ) : students.map((s: any) => (
              <tr key={s.student_id} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-medium text-slate-900 sticky left-0 bg-white">{s.student_name}</td>
                {concepts.map((c: any) => {
                  const masteryList = s.mastery ?? s.concept_mastery ?? []
                  const m = masteryList.find((x: any) => x.concept_id === c.id)
                  const val = m?.p_know ?? null
                  return (
                    <td key={c.id} className="px-3 py-2 text-center">
                      {val !== null ? (
                        <span className={`inline-block px-2 py-1 rounded text-xs font-semibold ${masteryColor(val)}`}>
                          {Math.round(val * 100)}%
                        </span>
                      ) : (
                        <span className="text-slate-300">—</span>
                      )}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 mt-4 text-xs text-slate-600">
        <span className="flex items-center gap-1.5"><span className="w-4 h-4 rounded bg-green-100 border border-green-200 inline-block" /> ≥80% Mastered</span>
        <span className="flex items-center gap-1.5"><span className="w-4 h-4 rounded bg-amber-100 border border-amber-200 inline-block" /> 50–79% Developing</span>
        <span className="flex items-center gap-1.5"><span className="w-4 h-4 rounded bg-red-100 border border-red-200 inline-block" /> &lt;50% Gap</span>
      </div>
    </div>
  )
}
