import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { useI18n } from '@/i18n/I18nProvider'

interface SubjectProgress {
  subject_id: string; name_en: string; name_te?: string; name_hi?: string
  concepts: number; studied: number; mastered: number; needs_improvement: number
  chapters_total: number; chapters_completed: number; progress_pct: number
}

/** Real per-subject progress from /students/{id}/subjects/progress (mastered concepts / concepts in subject). */
export default function SubjectProgressCard() {
  const { lang } = useI18n()
  const user = useAuthStore((s) => s.user)
  const { data } = useQuery<SubjectProgress[]>({
    queryKey: ['subject-progress', user?.id],
    queryFn: async () => (await api.get(`/students/${user?.id}/subjects/progress`)).data,
    enabled: !!user?.id,
  })
  if (!data?.length) return null
  return (
    <div className="card p-4 rounded-xl border border-slate-200 bg-white">
      <div className="grid sm:grid-cols-2 gap-3">
        {data.map((s) => (
          <Link key={s.subject_id} to="/student/learn" onClick={() => localStorage.setItem('chatur_subject', s.subject_id)}
            className="block p-3 rounded-lg border border-slate-200 hover:bg-slate-50">
            <div className="flex justify-between text-sm font-semibold text-slate-900">
              <span>{(lang === 'te' && s.name_te) || (lang === 'hi' && s.name_hi) || s.name_en}</span>
              <span>{s.progress_pct}%</span>
            </div>
            <div className="h-1.5 bg-slate-100 rounded mt-2"><div className="h-1.5 bg-indigo-600 rounded" style={{ width: `${s.progress_pct}%` }} /></div>
            <p className="text-xs text-slate-500 mt-2">
              {s.mastered}/{s.concepts} concepts mastered · {s.studied} studied · {s.needs_improvement} to improve · {s.chapters_completed}/{s.chapters_total} chapters
            </p>
          </Link>
        ))}
      </div>
    </div>
  )
}
