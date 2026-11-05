import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { 
  TrendingUp, 
  Flame, 
  Star, 
  Award, 
  BookOpen, 
  CheckCircle2, 
  Clock, 
  AlertCircle,
  ArrowRight,
  BrainCircuit,
  BarChart3
} from 'lucide-react'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { useI18n } from '@/i18n/I18nProvider'
import LoadingSpinner from '@/components/LoadingSpinner'
import ErrorMessage from '@/components/ErrorMessage'

interface SubjectBreakdown {
  subject_id: string
  subject_name: string
  total_concepts: number
  mastered_concepts: number
  in_progress_concepts: number
  average_p_know: number
}

interface ActivityItem {
  activity_type: string
  title: string
  score: number | null
  total_questions: number | null
  timestamp: string
}

interface ProgressSummary {
  student_id: string
  name: string
  grade: number
  total_xp: number
  current_streak: number
  overall_mastery: number
  subject_breakdown: SubjectBreakdown[]
  recent_activity: ActivityItem[]
  bkt_summary: {
    mastered: number
    proficient: number
    learning: number
    needs_attention: number
  }
}

export default function StudentProgress() {
  const { t } = useI18n()
  const user = useAuthStore((s) => s.user)

  const { data, isLoading, isError, refetch } = useQuery<ProgressSummary>({
    queryKey: ['student-progress-summary', user?.id],
    queryFn: async () => {
      const res = await api.get(`/students/${user?.id}/progress/summary`)
      return res.data
    },
    enabled: !!user?.id,
  })

  if (isLoading) return <LoadingSpinner />
  if (isError || !data) return <ErrorMessage onRetry={refetch} />

  const overallPct = Math.round(data.overall_mastery * 100)
  const totalTracked = 
    data.bkt_summary.mastered + 
    data.bkt_summary.proficient + 
    data.bkt_summary.learning + 
    data.bkt_summary.needs_attention

  return (
    <div className="p-4 lg:p-8 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="border-b border-[#ccd5ae] pb-4">
        <h1 className="text-2xl font-black text-[#000000] flex items-center gap-2">
          <TrendingUp className="w-6 h-6 text-[#000000]" />
          My Progress
        </h1>
        <p className="text-xs sm:text-sm text-[#333333] mt-1">
          Academic progress and concept mastery tracking for {data.name || user?.username} (Class {data.grade})
        </p>
      </div>

      {/* Top Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-[#ccd5ae] p-5 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-[#333333]">Overall Mastery</div>
            <div className="text-3xl font-black text-[#000000] mt-1">{overallPct}%</div>
            <div className="text-xs text-[#333333] mt-1">Across all enrolled subjects</div>
          </div>
          <div className="w-12 h-12 rounded-xl bg-[#faedcd] flex items-center justify-center text-[#000000] border border-[#ccd5ae]">
            <TrendingUp className="w-6 h-6 text-[#000000]" />
          </div>
        </div>

        <div className="bg-white rounded-xl border border-[#ccd5ae] p-5 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-[#333333]">Total XP Earned</div>
            <div className="text-3xl font-black text-[#000000] mt-1">{data.total_xp}</div>
            <div className="text-xs text-[#333333] mt-1">Knowledge Points</div>
          </div>
          <div className="w-12 h-12 rounded-xl bg-[#faedcd] flex items-center justify-center text-[#000000] border border-[#ccd5ae]">
            <Star className="w-6 h-6 text-[#000000]" />
          </div>
        </div>

        <div className="bg-white rounded-xl border border-[#ccd5ae] p-5 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-[#333333]">Daily Streak</div>
            <div className="text-3xl font-black text-[#000000] mt-1">
              {data.current_streak} <span className="text-sm font-bold text-[#333333]">days</span>
            </div>
            <div className="text-xs text-[#333333] mt-1">Consistent learner</div>
          </div>
          <div className="w-12 h-12 rounded-xl bg-[#faedcd] flex items-center justify-center text-[#000000] border border-[#ccd5ae]">
            <Flame className="w-6 h-6 text-[#000000]" />
          </div>
        </div>

        <div className="bg-white rounded-xl border border-[#ccd5ae] p-5 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-[#333333]">Mastered Concepts</div>
            <div className="text-3xl font-black text-[#000000] mt-1">{data.bkt_summary.mastered}</div>
            <div className="text-xs text-[#333333] mt-1">High confidence (≥80%)</div>
          </div>
          <div className="w-12 h-12 rounded-xl bg-[#faedcd] flex items-center justify-center text-[#000000] border border-[#ccd5ae]">
            <Award className="w-6 h-6 text-[#000000]" />
          </div>
        </div>
      </div>

      {/* Bayesian Knowledge Tracing Distribution */}
      <div className="bg-white rounded-xl border border-[#ccd5ae] p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[#ccd5ae] gap-2">
          <div>
            <h2 className="text-base font-bold text-[#000000] flex items-center gap-2">
              <BrainCircuit className="w-5 h-5 text-[#000000]" />
              Concept Mastery Levels
            </h2>
            <p className="text-xs text-[#333333] mt-0.5">
              Concept understanding evaluated from reading lessons, answering practice questions, and weekly test results.
            </p>
          </div>
          <span className="text-xs font-bold px-2.5 py-1 rounded bg-[#faedcd] text-[#000000] border border-[#ccd5ae]">
            {totalTracked} concepts evaluated
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-5">
          <div className="p-4 rounded-xl bg-[#e9edc9]/60 border border-[#ccd5ae]">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[#000000]">Mastered (≥80%)</span>
              <CheckCircle2 className="w-4 h-4 text-[#000000]" />
            </div>
            <div className="text-2xl font-black text-[#000000] mt-2">{data.bkt_summary.mastered}</div>
            <div className="text-xs text-[#333333] mt-1">Ready for advanced practice</div>
          </div>

          <div className="p-4 rounded-xl bg-[#faedcd]/60 border border-[#ccd5ae]">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[#000000]">Proficient (60-79%)</span>
              <BarChart3 className="w-4 h-4 text-[#000000]" />
            </div>
            <div className="text-2xl font-black text-[#000000] mt-2">{data.bkt_summary.proficient}</div>
            <div className="text-xs text-[#333333] mt-1">Good foundation</div>
          </div>

          <div className="p-4 rounded-xl bg-[#faedcd]/40 border border-[#ccd5ae]">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[#000000]">Learning (35-59%)</span>
              <Clock className="w-4 h-4 text-[#000000]" />
            </div>
            <div className="text-2xl font-black text-[#000000] mt-2">{data.bkt_summary.learning}</div>
            <div className="text-xs text-[#333333] mt-1">In progress</div>
          </div>

          <div className="p-4 rounded-xl bg-[#faedcd]/20 border border-[#ccd5ae]">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[#000000]">Needs Attention (&lt;35%)</span>
              <AlertCircle className="w-4 h-4 text-[#000000]" />
            </div>
            <div className="text-2xl font-black text-[#000000] mt-2">{data.bkt_summary.needs_attention}</div>
            <div className="text-xs text-[#333333] mt-1">Revisit lesson & practice</div>
          </div>
        </div>
      </div>

      {/* Subject-Wise Performance Breakdown */}
      <div>
        <h2 className="text-base font-bold text-[#000000] mb-4 flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-[#000000]" />
          Subject-Wise Progress
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {data.subject_breakdown.map((sb) => {
            const avgPct = Math.round(sb.average_p_know * 100)
            const completionPct = sb.total_concepts > 0 
              ? Math.round((sb.mastered_concepts / sb.total_concepts) * 100) 
              : 0

            return (
              <div 
                key={sb.subject_id} 
                className="bg-white rounded-xl border border-[#ccd5ae] p-5 shadow-sm hover:border-[#d4a373] transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <h3 className="font-bold text-[#000000] text-base">{sb.subject_name}</h3>
                    <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-[#e9edc9] text-[#000000] border border-[#ccd5ae]">
                      {avgPct}% Mastery
                    </span>
                  </div>

                  {/* Progress Bar */}
                  <div className="mt-4">
                    <div className="flex justify-between text-xs text-[#333333] mb-1.5">
                      <span>Concept Progress</span>
                      <span className="font-bold text-[#000000]">
                        {sb.mastered_concepts} / {sb.total_concepts} Mastered
                      </span>
                    </div>
                    <div className="w-full bg-[#e9edc9] rounded-full h-2.5 overflow-hidden border border-[#ccd5ae]">
                      <div 
                        className="bg-[#d4a373] h-2.5 rounded-full transition-all duration-500"
                        style={{ width: `${completionPct}%` }}
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2 mt-4 text-center">
                    <div className="p-2 rounded-lg bg-[#faedcd]/40 border border-[#ccd5ae]">
                      <div className="text-[10px] uppercase font-bold text-[#333333]">Total</div>
                      <div className="text-sm font-bold text-[#000000]">{sb.total_concepts}</div>
                    </div>
                    <div className="p-2 rounded-lg bg-[#e9edc9]/50 border border-[#ccd5ae]">
                      <div className="text-[10px] uppercase font-bold text-[#000000]">Mastered</div>
                      <div className="text-sm font-bold text-[#000000]">{sb.mastered_concepts}</div>
                    </div>
                    <div className="p-2 rounded-lg bg-[#faedcd]/80 border border-[#ccd5ae]">
                      <div className="text-[10px] uppercase font-bold text-[#333333]">Active</div>
                      <div className="text-sm font-bold text-[#000000]">{sb.in_progress_concepts}</div>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-end gap-3 mt-5 pt-3 border-t border-[#ccd5ae]">
                  <Link
                    to={`/student/learn?subject_id=${sb.subject_id}`}
                    className="text-xs font-bold text-[#000000] hover:underline flex items-center gap-1"
                  >
                    View Lessons <ArrowRight className="w-3.5 h-3.5 text-[#000000]" />
                  </Link>
                  <Link
                    to={`/student/practice?subject_id=${sb.subject_id}`}
                    className="btn-primary text-xs px-3 py-1.5 font-bold"
                  >
                    Practise
                  </Link>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Recent Activity Log */}
      <div className="bg-white rounded-xl border border-[#ccd5ae] p-6 shadow-sm">
        <h2 className="text-base font-bold text-[#000000] mb-4 flex items-center gap-2">
          <Clock className="w-5 h-5 text-[#000000]" />
          Recent Academic Activity
        </h2>

        {(!data.recent_activity || data.recent_activity.length === 0) ? (
          <div className="text-center py-8 text-[#333333] text-sm">
            No recent activity recorded yet. Start a lesson or practice session to view your history!
          </div>
        ) : (
          <div className="divide-y divide-[#ccd5ae]">
            {data.recent_activity.map((act, idx) => {
              const dateStr = act.timestamp ? new Date(act.timestamp).toLocaleDateString() : 'Recent'
              const isTest = act.activity_type.toLowerCase().includes('test')
              const isPractice = act.activity_type.toLowerCase().includes('practice')
              
              return (
                <div key={idx} className="py-3.5 flex items-center justify-between hover:bg-[#faedcd]/30 px-2 rounded-lg transition-colors">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold border border-[#ccd5ae] ${
                      isTest ? 'bg-[#faedcd] text-[#000000]' :
                      isPractice ? 'bg-[#e9edc9] text-[#000000]' :
                      'bg-white text-[#000000]'
                    }`}>
                      {isTest ? 'TEST' : isPractice ? 'PRAC' : 'LESS'}
                    </div>
                    <div>
                      <div className="text-sm font-bold text-[#000000]">{act.title}</div>
                      <div className="text-xs text-[#333333]">{dateStr} • {act.activity_type}</div>
                    </div>
                  </div>

                  <div className="text-right">
                    {act.score !== null && act.total_questions !== null ? (
                      <div>
                        <span className="text-sm font-black text-[#000000]">{act.score}</span>
                        <span className="text-xs text-[#333333]"> / {act.total_questions}</span>
                      </div>
                    ) : (
                      <span className="text-xs text-[#000000] font-bold">Completed</span>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
