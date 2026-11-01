import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Users, BookCheck, Printer, X, Sparkles } from 'lucide-react'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { useI18n } from '@/i18n/I18nProvider'
import PageHeader from '@/components/PageHeader'
import LoadingSpinner from '@/components/LoadingSpinner'
import ErrorMessage from '@/components/ErrorMessage'

export default function TeacherGroups() {
  const { t } = useI18n()
  const user = useAuthStore((s) => s.user)
  const [activeWorksheet, setActiveWorksheet] = useState<any | null>(null)

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['remedial-groups', user?.id],
    queryFn: async () => {
      const res = await api.get(`/teachers/${user?.id}/remedial-groups`)
      return res.data
    },
    enabled: !!user?.id,
  })

  if (isLoading) return <LoadingSpinner />
  if (isError) return <ErrorMessage onRetry={refetch} />

  const groups: any[] = Array.isArray(data) ? data : (data?.groups ?? [])

  const handleGenerateWorksheet = (g: any) => {
    setActiveWorksheet({
      groupName: g.name,
      conceptName: g.concept_name || g.root_concept_name || 'Foundational Prerequisite',
      tier1: [
        '1. State the SI unit of measurement for this concept.',
        '2. Convert 10 km/h into metres per second (m/s).',
        '3. Identify whether a stationary bus has non-zero velocity or acceleration.',
      ],
      tier2: [
        '4. A car moves 150 km in 2.5 hours. Calculate its average velocity in SI units.',
        '5. Draw and label a distance-time graph representing an object in uniform motion.',
      ],
      tier3: [
        '6. An object accelerates uniformly from rest at 2.5 m/s² for 8 seconds. Compute total displacement.',
        '7. Distinguish between uniform speed and uniform acceleration with a concrete real-world example.',
      ],
    })
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <PageHeader title={t('nav_groups')} subtitle="Students grouped by shared prerequisite gaps" />

      {/* Printable Worksheet Modal */}
      {activeWorksheet && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-2xl w-full p-6 space-y-5 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b pb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-primary-700" />
                <h3 className="text-lg font-bold text-slate-900">
                  Differentiated Worksheet: {activeWorksheet.conceptName}
                </h3>
              </div>
              <button
                onClick={() => setActiveWorksheet(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-3 bg-slate-50 rounded-lg text-xs text-slate-600 flex justify-between">
              <span><b>Target Remedial Group:</b> {activeWorksheet.groupName}</span>
              <span><b>Class Tier:</b> 3-Level Differentiated</span>
            </div>

            <div className="space-y-4 text-sm text-slate-800">
              <div className="p-3 rounded-lg border border-amber-200 bg-amber-50/50 space-y-2">
                <span className="font-bold text-amber-900 text-xs uppercase tracking-wider block">
                  Level 1 — Foundational Basics (Recall & Units)
                </span>
                {activeWorksheet.tier1.map((item: string, i: number) => (
                  <p key={i} className="text-xs text-slate-800">{item}</p>
                ))}
              </div>

              <div className="p-3 rounded-lg border border-blue-200 bg-blue-50/50 space-y-2">
                <span className="font-bold text-blue-900 text-xs uppercase tracking-wider block">
                  Level 2 — Working Grade Practice (Graphs & Application)
                </span>
                {activeWorksheet.tier2.map((item: string, i: number) => (
                  <p key={i} className="text-xs text-slate-800">{item}</p>
                ))}
              </div>

              <div className="p-3 rounded-lg border border-purple-200 bg-purple-50/50 space-y-2">
                <span className="font-bold text-purple-900 text-xs uppercase tracking-wider block">
                  Level 3 — Challenge & Stretch (Synthesis & Word Problems)
                </span>
                {activeWorksheet.tier3.map((item: string, i: number) => (
                  <p key={i} className="text-xs text-slate-800">{item}</p>
                ))}
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t">
              <button
                onClick={() => setActiveWorksheet(null)}
                className="btn-secondary text-xs px-4 py-2"
              >
                Close
              </button>
              <button
                onClick={() => window.print()}
                className="btn-primary text-xs px-4 py-2 inline-flex items-center gap-1.5"
              >
                <Printer className="w-4 h-4" />
                <span>{t('print')} Worksheet</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {groups.length === 0 ? (
        <div className="card p-8 text-center">
          <Users className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <p className="text-slate-500">{t('no_data')}</p>
          <p className="text-sm text-slate-400 mt-1">
            Remedial groups are automatically formed when multiple students share the same prerequisite gap.
          </p>
        </div>
      ) : (
        <div className="grid gap-4">
          {groups.map((g: any) => (
            <div key={g.id} className="card p-5 space-y-3 bg-white border border-slate-200 rounded-xl shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-slate-900 text-base">{g.name}</h3>
                  <p className="text-sm text-slate-500 mt-0.5">
                    Root Prerequisite Gap:{' '}
                    <span className="text-amber-800 font-medium">
                      {g.concept_name || g.root_concept_name || 'Foundational Prerequisite'}
                    </span>
                  </p>
                </div>
                <span className="badge badge-blue">{g.member_count} students</span>
              </div>

              <div className="flex flex-wrap gap-2 pt-2">
                {(g.members ?? []).map((m: any) => (
                  <span key={m.student_id || m} className="badge badge-slate">
                    {m.student_name || m}
                  </span>
                ))}
              </div>

              <div className="flex gap-2 pt-2 border-t border-slate-100">
                <button
                  onClick={() => handleGenerateWorksheet(g)}
                  className="btn-accent text-xs py-1.5 px-3 rounded-lg inline-flex items-center gap-1.5"
                >
                  <BookCheck className="w-3.5 h-3.5" />
                  <span>Generate Differentiated Worksheet</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

