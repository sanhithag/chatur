import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  BookOpen,
  Target,
  FileCheck,
  CheckSquare,
  Square,
  ChevronRight,
  Play,
  ArrowRight,
  TrendingUp,
} from 'lucide-react'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { useI18n } from '@/i18n/I18nProvider'
import LoadingSpinner from '@/components/LoadingSpinner'
import ErrorMessage from '@/components/ErrorMessage'

function MasteryBar({ value }: { value: number }) {
  const pct = Math.round(value * 100)
  return (
    <div className="flex items-center gap-2">
      <div className="w-full bg-[#e9edc9] rounded-full h-2 overflow-hidden flex-1 border border-[#ccd5ae]">
        <div
          className="h-full bg-[#d4a373] transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-semibold text-[#000000] w-9 text-right">{pct}%</span>
    </div>
  )
}

export default function StudentDashboard() {
  const { t } = useI18n()
  const user = useAuthStore((s) => s.user)
  const [lastConcept, setLastConcept] = useState<{ id: string; name: string } | null>(null)

  useEffect(() => {
    try {
      const stored = localStorage.getItem('chatur_last_concept')
      if (stored) {
        setLastConcept(JSON.parse(stored))
      }
    } catch {
      // ignore
    }
  }, [])

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['student-dashboard', user?.id],
    queryFn: async () => {
      const res = await api.get(`/students/${user?.id}/dashboard`)
      return res.data
    },
    enabled: !!user?.id,
  })

  // To-do task completion toggle
  const handleToggleTask = async (taskId: string, currentCompleted: boolean) => {
    try {
      await api.patch(`/students/${user?.id}/tasks/${taskId}`, {
        is_completed: !currentCompleted,
      })
      refetch()
    } catch (err) {
      console.error('Failed to toggle task:', err)
    }
  }

  if (isLoading) return <LoadingSpinner />
  if (isError) return <ErrorMessage onRetry={refetch} />

  const student = data?.student
  const mastery: Array<{ concept_id: string; concept_name: string; p_know: number }> =
    data?.mastery_summary ?? []
  const subjects: Array<{ subject_id: string; subject_name: string; concepts_in_progress: number }> =
    data?.enrolled_subjects ?? []
  const pendingTasks: Array<any> = data?.pending_tasks ?? []

  return (
    <div className="max-w-6xl mx-auto py-6 px-4 space-y-6 text-[#000000]">
      {/* Page Header */}
      <div className="border-b border-[#ccd5ae] pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#000000]">
            Welcome, {student?.name ?? user?.username}!
          </h1>
          <p className="text-xs text-[#333333] mt-0.5">
            Class {student?.grade ?? 10}-{student?.section ?? 'A'} &bull; CBSE Curriculum
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link to="/student/learn" className="btn-secondary text-xs">
            <BookOpen className="w-3.5 h-3.5" />
            Curriculum
          </Link>
          <Link to="/student/practice" className="btn-primary text-xs">
            <Target className="w-3.5 h-3.5" />
            Practise
          </Link>
        </div>
      </div>

      {/* Continue Learning Banner (Active Topic) */}
      {lastConcept && (
        <div className="bg-[#faedcd] border border-[#ccd5ae] rounded-lg p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-[#000000]">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#333333] flex items-center gap-1.5">
              <Play className="w-3 h-3 text-[#000000] fill-current" /> Continue Learning
            </span>
            <h3 className="text-base font-bold text-[#000000] mt-0.5">{lastConcept.name}</h3>
          </div>
          <div className="flex items-center gap-2">
            <Link
              to={`/student/learn?concept_id=${lastConcept.id}`}
              className="btn-primary text-xs"
            >
              Resume Lesson
            </Link>
            <Link
              to={`/student/practice?concept_id=${lastConcept.id}`}
              className="btn-secondary text-xs"
            >
              Practise Topic
            </Link>
          </div>
        </div>
      )}

      {/* Key Overview Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-white rounded-lg border border-[#ccd5ae] p-3.5 text-[#000000]">
          <div className="text-xs text-[#333333] font-medium">Total XP</div>
          <div className="text-xl font-bold text-[#000000] mt-0.5">{student?.total_xp ?? 0}</div>
        </div>

        <div className="bg-white rounded-lg border border-[#ccd5ae] p-3.5 text-[#000000]">
          <div className="text-xs text-[#333333] font-medium">Daily Streak</div>
          <div className="text-xl font-bold text-[#000000] mt-0.5">{student?.current_streak ?? 0} days</div>
        </div>

        <div className="bg-white rounded-lg border border-[#ccd5ae] p-3.5 text-[#000000]">
          <div className="text-xs text-[#333333] font-medium">Enrolled Subjects</div>
          <div className="text-xl font-bold text-[#000000] mt-0.5">{subjects.length}</div>
        </div>

        <div className="bg-white rounded-lg border border-[#ccd5ae] p-3.5 text-[#000000]">
          <div className="text-xs text-[#333333] font-medium">Tracked Concepts</div>
          <div className="text-xl font-bold text-[#000000] mt-0.5">{mastery.length}</div>
        </div>
      </div>

      {/* Structured Dashboard Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Columns: Pending Activities + Progress */}
        <div className="lg:col-span-2 space-y-6">
          {/* Pending Learning Activities (To-Do List) */}
          <div className="bg-white rounded-lg border border-[#ccd5ae] overflow-hidden text-[#000000]">
            <div className="p-3.5 border-b border-[#ccd5ae] bg-[#faedcd]/40 flex items-center justify-between">
              <h2 className="text-xs font-bold uppercase tracking-wider text-[#000000] flex items-center gap-1.5">
                <CheckSquare className="w-4 h-4 text-[#000000]" />
                Pending Learning Activities
              </h2>
              <Link to="/student/tasks" className="text-xs font-semibold text-[#000000] underline hover:text-[#d4a373]">
                Manage To-Do List &rarr;
              </Link>
            </div>
            <div className="p-3 divide-y divide-[#ccd5ae]/40">
              {pendingTasks.length === 0 ? (
                <div className="py-6 text-center text-xs text-[#333333]">
                  No pending learning activities. Check off completed items or add new study goals!
                </div>
              ) : (
                pendingTasks.map((t) => (
                  <div key={t.id} className="py-2.5 flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <button
                        type="button"
                        onClick={() => handleToggleTask(t.id, t.is_completed)}
                        className="text-[#333333] hover:text-[#000000] shrink-0 cursor-pointer"
                      >
                        {t.is_completed ? (
                          <CheckSquare className="w-4 h-4 text-[#d4a373]" />
                        ) : (
                          <Square className="w-4 h-4" />
                        )}
                      </button>
                      <span className={`text-xs font-medium text-[#000000] truncate ${t.is_completed ? 'line-through text-[#666666]' : ''}`}>
                        {t.title}
                      </span>
                    </div>
                    <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-[#e9edc9] text-[#000000] border border-[#ccd5ae] shrink-0">
                      {t.task_type}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Curriculum Mastery Progress */}
          <div className="bg-white rounded-lg border border-[#ccd5ae] overflow-hidden text-[#000000]">
            <div className="p-3.5 border-b border-[#ccd5ae] bg-[#faedcd]/40 flex items-center justify-between">
              <h2 className="text-xs font-bold uppercase tracking-wider text-[#000000] flex items-center gap-1.5">
                <TrendingUp className="w-4 h-4 text-[#000000]" />
                Concept Mastery Progress
              </h2>
              <Link to="/student/progress" className="text-xs font-semibold text-[#000000] underline hover:text-[#d4a373]">
                Full Progress &rarr;
              </Link>
            </div>
            <div className="p-3.5 space-y-3">
              {mastery.length === 0 ? (
                <p className="text-xs text-[#333333] py-4 text-center">No concept mastery data recorded yet.</p>
              ) : (
                mastery.slice(0, 5).map((m) => (
                  <div key={m.concept_id} className="p-2.5 rounded border border-[#ccd5ae] bg-[#fefae0]/40">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs font-semibold text-[#000000]">{m.concept_name}</span>
                      <div className="flex items-center gap-1.5">
                        <Link
                          to={`/student/learn?concept_id=${m.concept_id}`}
                          className="text-[11px] px-2 py-0.5 rounded bg-white hover:bg-[#e9edc9] border border-[#ccd5ae] font-medium"
                        >
                          Learn
                        </Link>
                        <Link
                          to={`/student/practice?concept_id=${m.concept_id}`}
                          className="text-[11px] px-2 py-0.5 rounded bg-[#d4a373] text-[#000000] hover:bg-[#c49262] font-semibold"
                        >
                          Practise
                        </Link>
                      </div>
                    </div>
                    <MasteryBar value={m.p_know} />
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Enrolled Subjects & Weekly Test */}
        <div className="space-y-6">
          {/* Subject Overview */}
          <div className="bg-white rounded-lg border border-[#ccd5ae] overflow-hidden text-[#000000]">
            <div className="p-3.5 border-b border-[#ccd5ae] bg-[#faedcd]/40 flex items-center justify-between">
              <h2 className="text-xs font-bold uppercase tracking-wider text-[#000000]">
                Curriculum Subjects
              </h2>
              <Link to="/student/learn" className="text-xs font-semibold text-[#000000] underline hover:text-[#d4a373]">
                Browse
              </Link>
            </div>
            <div className="divide-y divide-[#ccd5ae]/40">
              {subjects.length === 0 ? (
                <div className="p-4 text-xs text-[#333333] text-center">No subjects loaded.</div>
              ) : (
                subjects.map((s) => (
                  <Link
                    key={s.subject_name}
                    to="/student/learn"
                    className="px-3.5 py-2.5 flex items-center justify-between hover:bg-[#fefae0] transition-colors"
                  >
                    <div>
                      <div className="text-xs font-semibold text-[#000000]">{s.subject_name}</div>
                      <div className="text-[11px] text-[#333333]">
                        {s.concepts_in_progress} concepts in progress
                      </div>
                    </div>
                    <ChevronRight className="w-3.5 h-3.5 text-[#333333]" />
                  </Link>
                ))
              )}
            </div>
          </div>

          {/* Upcoming Weekly Tests */}
          <div className="bg-white rounded-lg border border-[#ccd5ae] p-4 text-[#000000] space-y-3">
            <div className="flex items-center gap-2">
              <FileCheck className="w-5 h-5 text-[#d4a373]" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-[#000000]">
                Weekly Assessment
              </h3>
            </div>
            <p className="text-xs text-[#333333]">
              Regular weekly tests assess your concept mastery and retention across all covered NCERT chapters.
            </p>
            <Link
              to="/student/test"
              className="w-full btn-primary text-xs py-2"
            >
              Take Weekly Test
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
