import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { useI18n } from '@/i18n/I18nProvider'

interface Subject { id: string; code: string; name_en: string; name_te?: string; name_hi?: string }
interface Concept { id: string; name_en: string; name_te?: string; name_hi?: string; lesson_ready: boolean }
interface Chapter { id: string; chapter_no: number; unit: string; name_en: string; name_te?: string; name_hi?: string; concepts: Concept[] }
interface Navigator { grades: number[]; grade: number; chapters: Chapter[] }

export interface NavSelection { subjectId: string | null; conceptId: string | null }

const loc = (o: { name_en: string; name_te?: string; name_hi?: string }, lang: string) =>
  (lang === 'te' && o.name_te) || (lang === 'hi' && o.name_hi) || o.name_en

/** Subject -> class -> chapter -> concept picker. All data comes from the backend; nothing hardcoded. */
export default function SubjectNavigator({ value, onChange }: { value: NavSelection; onChange: (v: NavSelection) => void }) {
  const { t, lang } = useI18n()
  const [grade, setGrade] = useState<number | undefined>()
  const [chapterId, setChapterId] = useState<string>('')

  const { data: subjects } = useQuery<Subject[]>({
    queryKey: ['curriculum-subjects'],
    queryFn: async () => (await api.get('/curriculum/subjects')).data,
  })
  const { data: nav } = useQuery<Navigator>({
    queryKey: ['subject-navigator', value.subjectId, grade],
    queryFn: async () => (await api.get(`/curriculum/subjects/${value.subjectId}/navigator`, { params: { grade } })).data,
    enabled: !!value.subjectId,
  })
  useEffect(() => { setChapterId('') }, [value.subjectId, grade])

  const chapter = nav?.chapters.find((c) => c.id === chapterId)
  const sel = 'border border-slate-300 rounded-lg px-2 py-1.5 text-sm bg-white'

  return (
    <div className="card p-4 rounded-xl border border-slate-200 bg-white space-y-3">
      <div className="flex flex-wrap gap-2">
        {subjects?.map((s) => (
          <button key={s.id} onClick={() => { setGrade(undefined); onChange({ subjectId: s.id, conceptId: null }) }}
            className={`px-3 py-1.5 rounded-full text-sm font-medium border ${value.subjectId === s.id ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'}`}>
            {loc(s, lang)}
          </button>
        ))}
      </div>
      {value.subjectId && nav && (
        <div className="flex flex-wrap gap-2 items-center">
          <label className="text-xs text-slate-500">{t('nav_class')}
            <select className={`${sel} ml-1`} value={nav.grade} onChange={(e) => setGrade(Number(e.target.value))}>
              {nav.grades.map((g) => <option key={g} value={g}>{g}</option>)}
            </select>
          </label>
          <label className="text-xs text-slate-500">{t('nav_chapter')}
            <select className={`${sel} ml-1 max-w-[16rem]`} value={chapterId} onChange={(e) => setChapterId(e.target.value)}>
              <option value="">{t('nav_recommended')}</option>
              {nav.chapters.map((c) => <option key={c.id} value={c.id}>{c.chapter_no}. {loc(c, lang)}</option>)}
            </select>
          </label>
          {chapter && (
            <label className="text-xs text-slate-500">{t('nav_concept')}
              <select className={`${sel} ml-1 max-w-[16rem]`} value={value.conceptId ?? ''} onChange={(e) => onChange({ subjectId: value.subjectId, conceptId: e.target.value || null })}>
                <option value="">—</option>
                {chapter.concepts.map((c) => <option key={c.id} value={c.id}>{loc(c, lang)}{c.lesson_ready ? '' : ' (soon)'}</option>)}
              </select>
            </label>
          )}
        </div>
      )}
    </div>
  )
}
