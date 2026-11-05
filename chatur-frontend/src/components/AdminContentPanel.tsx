import { useQuery, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'

interface Cov { subject: string; grade: number; concepts: number; with_lesson: number; validated: number; approved: number; translated_te: number; translated_hi: number }
interface Lesson { id: string; concept: string; code: string; status: string; validation?: { ok: boolean; issues: string[] }; content: { title: string; introduction: string } }

/** Coverage + review queue for AI-generated lessons. Approval re-runs automatic checks server-side. */
export default function AdminContentPanel() {
  const qc = useQueryClient()
  const { data: cov } = useQuery<Cov[]>({ queryKey: ['content-coverage'], queryFn: async () => (await api.get('/admin/content/coverage')).data })
  const { data: lessons } = useQuery<Lesson[]>({
    queryKey: ['content-lessons'],
    queryFn: async () => [...(await api.get('/admin/content/lessons', { params: { status: 'validated' } })).data, ...(await api.get('/admin/content/lessons', { params: { status: 'generated' } })).data],
  })
  const act = async (id: string, status: string) => {
    try { await api.post(`/admin/content/lessons/${id}/status`, { status }) } catch (e: any) { alert(JSON.stringify(e?.response?.data?.detail ?? 'Failed')) }
    qc.invalidateQueries({ queryKey: ['content-lessons'] }); qc.invalidateQueries({ queryKey: ['content-coverage'] })
  }
  return (
    <div className="card p-4 rounded-xl border border-slate-200 bg-white space-y-4">
      <h3 className="font-semibold text-slate-900">Content coverage</h3>
      <div className="overflow-x-auto"><table className="w-full text-xs text-left">
        <thead><tr className="text-slate-500"><th>Subject</th><th>Class</th><th>Concepts</th><th>Lessons</th><th>Validated</th><th>Approved</th><th>TE</th><th>HI</th></tr></thead>
        <tbody>{cov?.map((c) => <tr key={c.subject + c.grade} className="border-t"><td>{c.subject}</td><td>{c.grade}</td><td>{c.concepts}</td><td>{c.with_lesson}</td><td>{c.validated}</td><td>{c.approved}</td><td>{c.translated_te}</td><td>{c.translated_hi}</td></tr>)}</tbody>
      </table></div>
      <h3 className="font-semibold text-slate-900">Awaiting review ({lessons?.length ?? 0})</h3>
      {lessons?.map((l) => (
        <details key={l.id} className="border rounded-lg p-3 text-sm">
          <summary className="cursor-pointer flex justify-between"><span>{l.code} · {l.concept} <em className="text-xs text-slate-500">[{l.status}]</em></span></summary>
          <p className="mt-2 text-slate-600">{l.content.introduction}</p>
          {l.validation && !l.validation.ok && <ul className="text-xs text-red-600 list-disc pl-5">{l.validation.issues.map((i) => <li key={i}>{i}</li>)}</ul>}
          <button className="mt-2 px-3 py-1 rounded bg-emerald-600 text-white text-xs" onClick={() => act(l.id, 'approved')}>Approve</button>
        </details>
      ))}
      <p className="text-xs text-slate-500">AI-generated lessons are original explanations, not official NCERT/CBSE material, until reviewed by a human.</p>
    </div>
  )
}
