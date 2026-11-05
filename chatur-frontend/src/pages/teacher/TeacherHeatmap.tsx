import { useQuery } from '@tanstack/react-query'
import { LayoutGrid } from 'lucide-react'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { useI18n } from '@/i18n/I18nProvider'
import LoadingSpinner from '@/components/LoadingSpinner'
import ErrorMessage from '@/components/ErrorMessage'

function masteryColor(v: number | null): string {
  if (v === null || v === undefined) return 'bg-white text-[#333333] border border-[#ccd5ae]'
  if (v >= 0.8) return 'bg-[#e9edc9] text-[#000000] border border-[#ccd5ae] font-bold'
  if (v >= 0.5) return 'bg-[#faedcd] text-[#000000] border border-[#ccd5ae] font-bold'
  return 'bg-rose-100 text-rose-900 border border-rose-300 font-bold'
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
    <div className="p-4 lg:p-8 max-w-full space-y-6">
      <div className="border-b border-[#ccd5ae] pb-4">
        <h1 className="text-2xl font-black text-[#000000] flex items-center gap-2">
          <LayoutGrid className="w-6 h-6 text-[#000000]" />
          Concept Mastery Heatmap
        </h1>
        <p className="text-xs sm:text-sm text-[#333333] mt-1">
          Detailed concept mastery matrix across all students in your class.
        </p>
      </div>

      <div className="card bg-white border border-[#ccd5ae] overflow-x-auto shadow-sm">
        <table className="min-w-full text-xs">
          <thead>
            <tr className="bg-[#faedcd]/50 border-b border-[#ccd5ae]">
              <th className="px-4 py-3 text-left font-bold text-[#000000] sticky left-0 bg-[#faedcd] border-r border-[#ccd5ae]">
                Student
              </th>
              {concepts.map((c: any) => (
                <th key={c.id} className="px-3 py-3 text-center font-bold text-[#000000] min-w-[120px] border-r border-[#ccd5ae]">
                  <div className="leading-tight">
                    {c.name_en}
                    <div className="text-[10px] text-[#333333] font-medium">Gr {c.grade}</div>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[#ccd5ae]">
            {students.length === 0 ? (
              <tr>
                <td colSpan={concepts.length + 1} className="px-4 py-8 text-center text-[#333333]">
                  {t('no_data')}
                </td>
              </tr>
            ) : (
              students.map((s: any) => (
                <tr key={s.student_id} className="hover:bg-[#faedcd]/20 transition-colors">
                  <td className="px-4 py-3 font-bold text-[#000000] sticky left-0 bg-white border-r border-[#ccd5ae]">
                    {s.student_name}
                  </td>
                  {concepts.map((c: any) => {
                    const masteryList = s.mastery ?? s.concept_mastery ?? []
                    const m = masteryList.find((x: any) => x.concept_id === c.id)
                    const val = m?.p_know ?? null
                    return (
                      <td key={c.id} className="px-3 py-2 text-center border-r border-[#ccd5ae]">
                        {val !== null ? (
                          <span className={`inline-block px-2 py-0.5 rounded text-xs ${masteryColor(val)}`}>
                            {Math.round(val * 100)}%
                          </span>
                        ) : (
                          <span className="text-[#333333]">—</span>
                        )}
                      </td>
                    )
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 text-xs font-bold text-[#000000]">
        <span className="flex items-center gap-1.5">
          <span className="w-4 h-4 rounded bg-[#e9edc9] border border-[#ccd5ae] inline-block" />
          ≥80% Mastered
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-4 h-4 rounded bg-[#faedcd] border border-[#ccd5ae] inline-block" />
          50–79% Developing
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-4 h-4 rounded bg-rose-100 border border-rose-300 inline-block" />
          &lt;50% Needs Attention
        </span>
      </div>
    </div>
  )
}
