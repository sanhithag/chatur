import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  FileCheck,
  Clock,
  Calendar,
  History,
  CheckCircle2,
  XCircle,
  AlertCircle,
  ArrowRight,
  ArrowLeft,
  Send,
  Sparkles,
  ShieldAlert,
  Play,
  RotateCcw,
  Check,
} from 'lucide-react'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { useI18n } from '@/i18n/I18nProvider'
import LoadingSpinner from '@/components/LoadingSpinner'
import ErrorMessage from '@/components/ErrorMessage'

interface TestOverviewItem {
  id: string
  title: string
  assessment_type: string
  time_limit_mins: number
  total_questions: number
  subjects_covered: string[]
  status: 'available' | 'upcoming' | 'completed'
  scheduled_for?: string
}

interface TestHistoryItem {
  attempt_id: string
  assessment_id: string
  title: string
  score: number
  max_score: number
  accuracy_pct: number
  started_at: string
  completed_at?: string
  status: string
}

interface TestListResponse {
  available: TestOverviewItem[]
  upcoming: TestOverviewItem[]
  history: TestHistoryItem[]
}

interface TestItem {
  question_id: string
  concept_id: string
  concept_name: string
  section_type: 'working_level' | 'prereq_probe' | 'stretch'
  question_text: string
  options: string[]
}

interface TestPaper {
  assessment_id: string
  title: string
  time_limit_mins: number
  total_questions: number
  items: TestItem[]
}

interface TestSubmitResult {
  attempt_id?: string
  score: number
  max_score: number
  accuracy_pct: number
  feedback_message: string
  prerequisite_diagnosed?: string
  proposal_sent_to_teacher: boolean
}

interface TestAttemptReview {
  attempt_id: string
  assessment_id: string
  title: string
  score: number
  max_score: number
  accuracy_pct: number
  time_taken_mins: number
  completed_at: string
  questions: Array<{
    question_id: string
    concept_id: string
    concept_name: string
    section_type: string
    question_text: string
    options: string[]
    selected_option: number | null
    correct_option: number
    is_correct: boolean
    explanation: string
  }>
}

export default function StudentTest() {
  const { t, lang } = useI18n()
  const user = useAuthStore((s) => s.user)
  const queryClient = useQueryClient()

  // State Management
  const [activeTab, setActiveTab] = useState<'available' | 'upcoming' | 'history'>('available')
  const [selectedTestId, setSelectedTestId] = useState<string | null>(null)
  const [testState, setTestState] = useState<'idle' | 'instructions' | 'testing' | 'submitted' | 'reviewing'>('idle')
  const [currentIndex, setCurrentIndex] = useState<number>(0)
  const [answers, setAnswers] = useState<Record<string, number>>({})
  const [timeLeft, setTimeLeft] = useState<number>(0)
  const [isConfirmSubmitOpen, setIsConfirmSubmitOpen] = useState<boolean>(false)
  const [testResult, setTestResult] = useState<TestSubmitResult | null>(null)
  const [reviewAttemptId, setReviewAttemptId] = useState<string | null>(null)

  // 1. Fetch Weekly Assessments List
  const { data: testListData, isLoading: isLoadingList, refetch: refetchList } = useQuery<TestListResponse>({
    queryKey: ['weekly-tests-list', user?.id],
    queryFn: async () => {
      const res = await api.get(`/students/${user?.id}/tests/weekly`)
      return res.data
    },
    enabled: !!user?.id,
  })

  // 2. Fetch Test Paper when starting
  const { data: paper, isLoading: isLoadingPaper } = useQuery<TestPaper>({
    queryKey: ['test-paper', user?.id, selectedTestId, lang],
    queryFn: async () => {
      const res = await api.get(`/students/${user?.id}/tests/weekly/${selectedTestId}/start`, {
        params: { lang },
      })
      return res.data
    },
    enabled: !!user?.id && !!selectedTestId && testState === 'instructions',
  })

  // 3. Fetch Attempt Review
  const { data: reviewData, isLoading: isLoadingReview } = useQuery<TestAttemptReview>({
    queryKey: ['test-attempt-review', user?.id, reviewAttemptId],
    queryFn: async () => {
      const res = await api.get(`/students/${user?.id}/tests/weekly/attempts/${reviewAttemptId}/review`)
      return res.data
    },
    enabled: !!user?.id && !!reviewAttemptId && testState === 'reviewing',
  })

  // Submit Test Mutation
  const submitTestMutation = useMutation({
    mutationFn: async (): Promise<TestSubmitResult> => {
      if (!paper) throw new Error('No active paper')
      const formattedResponses = paper.items.map((item) => ({
        question_id: item.question_id,
        selected_option: answers[item.question_id] !== undefined ? answers[item.question_id] : null,
        time_spent_secs: 20,
      }))
      const res = await api.post(`/students/${user?.id}/tests/weekly/${paper.assessment_id}/submit`, {
        responses: formattedResponses,
      })
      return res.data as TestSubmitResult
    },
    onSuccess: (data) => {
      setTestResult(data)
      setIsConfirmSubmitOpen(false)
      setTestState('submitted')
      queryClient.invalidateQueries({ queryKey: ['weekly-tests-list', user?.id] })
      queryClient.invalidateQueries({ queryKey: ['student-dashboard', user?.id] })
    },
  })

  // Countdown timer for active assessment
  useEffect(() => {
    if (testState !== 'testing') return
    if (timeLeft <= 0) {
      if (paper && !submitTestMutation.isPending && !testResult) {
        submitTestMutation.mutate()
      }
      return
    }

    const timer = setInterval(() => {
      setTimeLeft((prev) => prev - 1)
    }, 1000)

    return () => clearInterval(timer)
  }, [testState, timeLeft, paper, submitTestMutation, testResult])

  const startTestFromInstructions = () => {
    setCurrentIndex(0)
    setAnswers({})
    setTimeLeft((paper?.time_limit_mins || 30) * 60)
    setTestState('testing')
  }

  const openAttemptReview = (attemptId: string) => {
    setReviewAttemptId(attemptId)
    setTestState('reviewing')
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  if (isLoadingList) return <LoadingSpinner />

  // ─── VIEW 1: INSTRUCTIONS VIEW ─────────────────────────────────────────────
  if (testState === 'instructions' && paper) {
    return (
      <div className="p-4 lg:p-8 max-w-3xl mx-auto space-y-6">
        <div className="card p-6 lg:p-8 bg-white border border-[#ccd5ae] space-y-6 shadow-sm">
          <div className="border-b border-[#ccd5ae] pb-4">
            <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-[#e9edc9] text-[#000000] border border-[#ccd5ae]">
              Assessment Instructions
            </span>
            <h1 className="text-2xl font-black text-[#000000] mt-2">{paper.title}</h1>
            <p className="text-xs sm:text-sm text-[#333333] mt-1">
              Read these guidelines carefully before launching your weekly assessment.
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 rounded-xl bg-[#faedcd] border border-[#ccd5ae] text-center">
              <Clock className="w-5 h-5 text-[#000000] mx-auto mb-1" />
              <div className="text-sm font-bold text-[#000000]">{paper.time_limit_mins} Mins</div>
              <div className="text-[10px] uppercase font-semibold text-[#333333]">Duration</div>
            </div>
            <div className="p-3 rounded-xl bg-[#faedcd] border border-[#ccd5ae] text-center">
              <FileCheck className="w-5 h-5 text-[#000000] mx-auto mb-1" />
              <div className="text-sm font-bold text-[#000000]">{paper.total_questions} Questions</div>
              <div className="text-[10px] uppercase font-semibold text-[#333333]">Questions</div>
            </div>
            <div className="p-3 rounded-xl bg-[#faedcd] border border-[#ccd5ae] text-center">
              <Sparkles className="w-5 h-5 text-[#000000] mx-auto mb-1" />
              <div className="text-sm font-bold text-[#000000]">Curriculum</div>
              <div className="text-[10px] uppercase font-semibold text-[#333333]">NCERT Blueprint</div>
            </div>
            <div className="p-3 rounded-xl bg-[#faedcd] border border-[#ccd5ae] text-center">
              <CheckCircle2 className="w-5 h-5 text-[#000000] mx-auto mb-1" />
              <div className="text-sm font-bold text-[#000000]">Auto-Scored</div>
              <div className="text-[10px] uppercase font-semibold text-[#333333]">Evaluated</div>
            </div>
          </div>

          <div className="space-y-3 text-xs sm:text-sm text-[#000000] bg-[#fefae0] p-4 rounded-xl border border-[#ccd5ae]">
            <h3 className="font-bold text-[#000000] text-xs uppercase tracking-wider">Exam Structure & Guidelines</h3>
            <ul className="list-disc pl-5 space-y-1.5 text-xs text-[#333333]">
              <li><strong className="text-[#000000]">Grade-Level Mastery:</strong> Questions assess current chapter understanding.</li>
              <li><strong className="text-[#000000]">Prerequisite Diagnostics:</strong> Includes foundational questions to identify concept gaps.</li>
              <li>Each question has exactly one correct answer. No negative marking.</li>
              <li>Your responses will automatically update your learning progress report.</li>
            </ul>
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-[#ccd5ae]">
            <button
              onClick={() => setTestState('idle')}
              className="btn-secondary text-xs"
            >
              Cancel
            </button>
            <button
              onClick={startTestFromInstructions}
              className="btn-primary text-sm px-6 py-2.5 font-bold cursor-pointer flex items-center gap-2"
            >
              <Play className="w-4 h-4 fill-current text-[#000000]" />
              <span>Begin Assessment Now</span>
            </button>
          </div>
        </div>
      </div>
    )
  }

  // ─── VIEW 2: ACTIVE TEST TAKING VIEW ───────────────────────────────────────
  if (testState === 'testing' && paper) {
    const currentQ = paper.items[currentIndex]
    const answeredCount = Object.keys(answers).length
    const currentAnswer = currentQ ? answers[currentQ.question_id] : undefined

    return (
      <div className="p-4 lg:p-8 max-w-5xl mx-auto space-y-6">
        {/* Sticky Exam Top Bar */}
        <div className="card p-4 bg-[#faedcd] text-[#000000] border border-[#ccd5ae] flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-3">
            <span className="w-8 h-8 rounded-lg bg-[#d4a373] text-[#000000] font-black flex items-center justify-center text-sm border border-[#ccd5ae]">
              Q
            </span>
            <div>
              <div className="text-sm font-bold text-[#000000] truncate max-w-md">{paper.title}</div>
              <div className="text-[11px] text-[#333333]">
                Question {currentIndex + 1} of {paper.total_questions} ({answeredCount} Answered)
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-mono font-bold ${
                timeLeft < 300
                  ? 'bg-rose-100 text-rose-900 border-rose-300 animate-pulse'
                  : 'bg-white text-[#000000] border-[#ccd5ae]'
              }`}
            >
              <Clock className="w-4 h-4 text-[#000000]" />
              <span>{formatTime(timeLeft)}</span>
            </div>

            <button
              onClick={() => setIsConfirmSubmitOpen(true)}
              className="btn-primary text-xs px-4 py-1.5 font-bold cursor-pointer"
            >
              Submit Test
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Main Question Workspace */}
          <div className="lg:col-span-3 space-y-6">
            <div className="card p-6 bg-white border border-[#ccd5ae] space-y-5">
              <div className="flex items-center justify-between border-b border-[#ccd5ae] pb-3">
                <span className="text-xs font-bold text-[#000000] uppercase tracking-wider">
                  {currentQ.concept_name}
                </span>
                <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-[#e9edc9] text-[#000000] border border-[#ccd5ae]">
                  {currentQ.section_type.replace('_', ' ')}
                </span>
              </div>

              <h2 className="text-base sm:text-lg font-bold text-[#000000] leading-relaxed">
                {currentQ.question_text}
              </h2>

              <div className="space-y-2.5">
                {currentQ.options.map((option, optIdx) => {
                  const isSelected = currentAnswer === optIdx
                  return (
                    <button
                      key={optIdx}
                      onClick={() =>
                        setAnswers((prev) => ({
                          ...prev,
                          [currentQ.question_id]: optIdx,
                        }))
                      }
                      className={`w-full text-left p-4 rounded-xl border text-sm transition-all flex items-center justify-between cursor-pointer ${
                        isSelected
                          ? 'bg-[#faedcd] border-2 border-[#d4a373] text-[#000000] font-bold shadow-xs'
                          : 'bg-white border-[#ccd5ae] text-[#000000] hover:bg-[#e9edc9]/50'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <span
                          className={`w-6 h-6 rounded-full text-xs font-bold flex items-center justify-center shrink-0 border ${
                            isSelected
                              ? 'bg-[#d4a373] text-[#000000] border-[#d4a373]'
                              : 'bg-[#faedcd] border-[#ccd5ae] text-[#000000]'
                          }`}
                        >
                          {String.fromCharCode(65 + optIdx)}
                        </span>
                        <span className="text-[#000000]">{option}</span>
                      </div>
                      {isSelected && <Check className="w-4 h-4 text-[#000000] shrink-0" />}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Stepper Navigation */}
            <div className="flex items-center justify-between">
              <button
                disabled={currentIndex === 0}
                onClick={() => setCurrentIndex((prev) => Math.max(0, prev - 1))}
                className="btn-secondary text-xs disabled:opacity-40"
              >
                <ArrowLeft className="w-3.5 h-3.5 text-[#000000]" /> Previous
              </button>

              {currentIndex === paper.total_questions - 1 ? (
                <button
                  onClick={() => setIsConfirmSubmitOpen(true)}
                  className="btn-primary text-xs px-6 py-2 font-bold cursor-pointer"
                >
                  Review & Submit
                </button>
              ) : (
                <button
                  onClick={() => setCurrentIndex((prev) => Math.min(paper.total_questions - 1, prev + 1))}
                  className="btn-primary text-xs px-6 py-2 font-bold cursor-pointer flex items-center gap-1.5"
                >
                  <span>Next Question</span>
                  <ArrowRight className="w-3.5 h-3.5 text-[#000000]" />
                </button>
              )}
            </div>
          </div>

          {/* Right Question Palette Drawer */}
          <div className="lg:col-span-1 space-y-4">
            <div className="card p-4 bg-white border border-[#ccd5ae] space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-[#000000]">
                Question Palette
              </h3>
              <div className="grid grid-cols-5 gap-2">
                {paper.items.map((it, idx) => {
                  const isAns = answers[it.question_id] !== undefined
                  const isCurrent = currentIndex === idx
                  return (
                    <button
                      key={it.question_id}
                      onClick={() => setCurrentIndex(idx)}
                      className={`h-9 rounded-lg font-bold text-xs transition-all cursor-pointer border ${
                        isCurrent
                          ? 'bg-[#d4a373] text-[#000000] border-[#000000]'
                          : isAns
                          ? 'bg-[#ccd5ae] text-[#000000] border-[#ccd5ae]'
                          : 'bg-white border-[#ccd5ae] text-[#333333] hover:bg-[#e9edc9]/50'
                      }`}
                    >
                      {idx + 1}
                    </button>
                  )
                })}
              </div>

              <div className="pt-3 border-t border-[#ccd5ae] space-y-1.5 text-[11px] text-[#333333]">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded bg-[#ccd5ae] border border-[#ccd5ae]" />
                  <span>Answered ({answeredCount})</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded bg-white border border-[#ccd5ae]" />
                  <span>Unanswered ({paper.total_questions - answeredCount})</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Submit Confirmation Dialog */}
        {isConfirmSubmitOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#000000]/40 backdrop-blur-xs animate-in fade-in">
            <div className="w-full max-w-md bg-white rounded-2xl p-6 shadow-xl border border-[#ccd5ae] space-y-4">
              <h3 className="text-lg font-bold text-[#000000]">Submit Weekly Assessment?</h3>
              <p className="text-xs sm:text-sm text-[#333333]">
                You have answered <strong className="text-[#000000]">{answeredCount}</strong> of{' '}
                <strong className="text-[#000000]">{paper.total_questions}</strong> questions.
                {paper.total_questions - answeredCount > 0 && (
                  <span className="block mt-1 text-rose-700 font-bold">
                    Warning: You still have {paper.total_questions - answeredCount} unanswered questions!
                  </span>
                )}
              </p>

              <div className="flex justify-end gap-3 pt-3 border-t border-[#ccd5ae]">
                <button
                  type="button"
                  onClick={() => setIsConfirmSubmitOpen(false)}
                  className="btn-secondary text-xs"
                >
                  Continue Testing
                </button>
                <button
                  type="button"
                  onClick={() => submitTestMutation.mutate()}
                  disabled={submitTestMutation.isPending}
                  className="btn-primary text-xs px-5 py-2 font-bold cursor-pointer"
                >
                  {submitTestMutation.isPending ? 'Scoring…' : 'Confirm Submission'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    )
  }

  // ─── VIEW 3: SUBMISSION REPORT & DIAGNOSTICS VIEW ──────────────────────────
  if (testState === 'submitted' && testResult) {
    return (
      <div className="p-4 lg:p-8 max-w-3xl mx-auto space-y-6">
        <div className="card p-8 bg-white border border-[#ccd5ae] text-center space-y-6 shadow-sm animate-in fade-in">
          <div className="w-16 h-16 rounded-full bg-[#e9edc9] text-[#000000] font-bold flex items-center justify-center mx-auto border-2 border-[#ccd5ae]">
            <CheckCircle2 className="w-8 h-8 text-[#000000]" />
          </div>

          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-[#e9edc9] text-[#000000] border border-[#ccd5ae]">
              Assessment Completed
            </span>
            <h1 className="text-3xl font-black text-[#000000] mt-2">Score Report</h1>
            <p className="text-xs sm:text-sm text-[#333333] mt-1">{testResult.feedback_message}</p>
          </div>

          <div className="p-6 rounded-2xl bg-[#faedcd] border border-[#ccd5ae] flex items-center justify-around">
            <div>
              <div className="text-3xl font-black text-[#000000]">{testResult.score} / {testResult.max_score}</div>
              <div className="text-[10px] uppercase font-bold text-[#333333] mt-0.5">Raw Score</div>
            </div>
            <div className="w-px h-10 bg-[#ccd5ae]" />
            <div>
              <div className="text-3xl font-black text-[#000000]">{testResult.accuracy_pct}%</div>
              <div className="text-[10px] uppercase font-bold text-[#333333] mt-0.5">Accuracy</div>
            </div>
          </div>

          {/* Diagnostic Remediation Card */}
          {testResult.prerequisite_diagnosed && (
            <div className="p-4 rounded-xl bg-[#faedcd]/60 border border-[#ccd5ae] text-left space-y-1.5">
              <div className="flex items-center gap-2 text-xs font-bold text-[#000000]">
                <ShieldAlert className="w-4 h-4 text-[#000000]" />
                Learning Recommendation
              </div>
              <p className="text-xs text-[#333333]">
                Prerequisite concept gap identified: <strong className="text-[#000000]">{testResult.prerequisite_diagnosed}</strong>.
                Recommended to revisit this concept in the Learn section.
              </p>
            </div>
          )}

          <div className="flex items-center justify-center gap-3 pt-2">
            <button
              onClick={() => {
                if (testResult.attempt_id) {
                  openAttemptReview(testResult.attempt_id)
                } else {
                  setTestState('idle')
                }
              }}
              className="btn-primary text-xs px-5 py-2.5 font-bold cursor-pointer"
            >
              Review All Answers
            </button>
            <button
              onClick={() => setTestState('idle')}
              className="btn-secondary text-xs px-5 py-2.5"
            >
              Return to Weekly Tests
            </button>
          </div>
        </div>
      </div>
    )
  }

  // ─── VIEW 4: DETAILED ANSWER REVIEW VIEW ───────────────────────────────────
  if (testState === 'reviewing') {
    if (isLoadingReview || !reviewData) return <LoadingSpinner />

    return (
      <div className="p-4 lg:p-8 max-w-4xl mx-auto space-y-6">
        <div className="flex items-center justify-between border-b border-[#ccd5ae] pb-4">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-[#e9edc9] text-[#000000] border border-[#ccd5ae]">
              Historical Attempt Review
            </span>
            <h1 className="text-2xl font-black text-[#000000] mt-1">{reviewData.title}</h1>
            <p className="text-xs text-[#333333]">
              Completed on {new Date(reviewData.completed_at).toLocaleDateString()} • Score: {reviewData.score} / {reviewData.max_score} ({reviewData.accuracy_pct}%)
            </p>
          </div>

          <button
            onClick={() => setTestState('idle')}
            className="btn-secondary text-xs"
          >
            Close Review
          </button>
        </div>

        {/* Question-by-Question Detailed Review */}
        <div className="space-y-4">
          {reviewData.questions.map((q, qIdx) => (
            <div
              key={q.question_id}
              className={`card p-5 border space-y-3 ${
                q.is_correct ? 'bg-[#e9edc9]/40 border-[#ccd5ae]' : 'bg-rose-50/50 border-rose-300'
              }`}
            >
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-[#000000]">Q{qIdx + 1}.</span>
                  <span className="font-semibold text-[#000000]">{q.concept_name}</span>
                </div>
                <span
                  className={`font-bold px-2 py-0.5 rounded text-[10px] uppercase border ${
                    q.is_correct ? 'bg-[#ccd5ae] text-[#000000] border-[#ccd5ae]' : 'bg-rose-100 text-rose-900 border-rose-300'
                  }`}
                >
                  {q.is_correct ? 'Correct' : 'Incorrect'}
                </span>
              </div>

              <p className="text-sm font-bold text-[#000000]">{q.question_text}</p>

              <div className="space-y-1.5 text-xs">
                {q.options.map((opt, oIdx) => {
                  let optStyle = 'bg-white border-[#ccd5ae] text-[#333333]'
                  if (oIdx === q.correct_option) {
                    optStyle = 'bg-[#e9edc9] border-2 border-[#ccd5ae] text-[#000000] font-bold'
                  } else if (oIdx === q.selected_option && !q.is_correct) {
                    optStyle = 'bg-rose-100 border-2 border-rose-300 text-rose-900 font-bold'
                  }
                  return (
                    <div key={oIdx} className={`p-3 rounded-lg border flex items-center justify-between ${optStyle}`}>
                      <span className="text-[#000000]">{opt}</span>
                      {oIdx === q.correct_option && (
                        <span className="text-[10px] font-bold uppercase text-[#000000]">Correct Answer</span>
                      )}
                      {oIdx === q.selected_option && !q.is_correct && (
                        <span className="text-[10px] font-bold uppercase text-rose-900">Your Choice</span>
                      )}
                    </div>
                  )
                })}
              </div>

              <div className="p-3 bg-white rounded-lg border border-[#ccd5ae] text-xs space-y-1">
                <span className="font-bold text-[#000000]">Explanation:</span>
                <p className="text-[#333333] leading-relaxed">{q.explanation}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  // ─── VIEW 5: DEFAULT HUB VIEW (AVAILABLE, UPCOMING, HISTORY) ───────────────
  return (
    <div className="p-4 lg:p-8 max-w-5xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#ccd5ae] pb-4">
        <div>
          <h1 className="text-2xl font-black text-[#000000] flex items-center gap-2">
            <FileCheck className="w-6 h-6 text-[#000000]" />
            Weekly Assessments
          </h1>
          <p className="text-xs sm:text-sm text-[#333333] mt-1">
            Weekly curriculum assessments to test concept retention and exam readiness.
          </p>
        </div>

        <div className="flex items-center gap-1.5 p-1 bg-[#faedcd] border border-[#ccd5ae] rounded-xl self-start sm:self-auto">
          <button
            onClick={() => setActiveTab('available')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              activeTab === 'available'
                ? 'bg-[#d4a373] text-[#000000] border border-[#ccd5ae]'
                : 'text-[#333333] hover:text-[#000000]'
            }`}
          >
            Available ({testListData?.available?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('upcoming')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              activeTab === 'upcoming'
                ? 'bg-[#d4a373] text-[#000000] border border-[#ccd5ae]'
                : 'text-[#333333] hover:text-[#000000]'
            }`}
          >
            Upcoming ({testListData?.upcoming?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              activeTab === 'history'
                ? 'bg-[#d4a373] text-[#000000] border border-[#ccd5ae]'
                : 'text-[#333333] hover:text-[#000000]'
            }`}
          >
            <History className="w-3.5 h-3.5" />
            Previous ({testListData?.history?.length || 0})
          </button>
        </div>
      </div>

      {/* ─── TAB: AVAILABLE TESTS ───────────────────────────────────────────── */}
      {activeTab === 'available' && (
        <div className="space-y-4">
          {testListData?.available?.map((tItem) => (
            <div
              key={tItem.id}
              className="card p-6 bg-white border border-[#ccd5ae] flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xs hover:border-[#d4a373] transition-all"
            >
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-[#e9edc9] text-[#000000] border border-[#ccd5ae]">
                    Active Test
                  </span>
                  <span className="text-xs text-[#333333]">
                    {tItem.total_questions} Questions • {tItem.time_limit_mins} Mins Duration
                  </span>
                </div>
                <h3 className="text-base sm:text-lg font-bold text-[#000000]">{tItem.title}</h3>
                <div className="flex items-center gap-2 text-xs text-[#333333] flex-wrap">
                  <span className="font-semibold text-[#000000]">Subjects:</span>
                  {tItem.subjects_covered.map((s, i) => (
                    <span key={i} className="px-2 py-0.5 rounded bg-[#faedcd] border border-[#ccd5ae] text-[#000000]">
                      {s}
                    </span>
                  ))}
                </div>
              </div>

              <button
                onClick={() => {
                  setSelectedTestId(tItem.id)
                  setTestState('instructions')
                }}
                className="btn-primary text-xs px-5 py-2.5 font-bold cursor-pointer shrink-0 flex items-center justify-center gap-2"
              >
                <Play className="w-3.5 h-3.5 fill-current text-[#000000]" />
                <span>Start Test</span>
              </button>
            </div>
          ))}
        </div>
      )}

      {/* ─── TAB: UPCOMING TESTS ────────────────────────────────────────────── */}
      {activeTab === 'upcoming' && (
        <div className="space-y-4">
          {testListData?.upcoming?.map((uItem) => (
            <div
              key={uItem.id}
              className="card p-6 bg-[#faedcd]/40 border border-[#ccd5ae] flex flex-col sm:flex-row sm:items-center justify-between gap-4"
            >
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-[#ccd5ae] text-[#000000]">
                    Scheduled Test
                  </span>
                  <span className="text-xs text-[#333333]">
                    {uItem.scheduled_for ? new Date(uItem.scheduled_for).toLocaleDateString() : 'Coming Soon'}
                  </span>
                </div>
                <h3 className="text-base font-bold text-[#000000]">{uItem.title}</h3>
                <p className="text-xs text-[#333333]">
                  {uItem.time_limit_mins} mins • {uItem.total_questions} questions across {uItem.subjects_covered.join(', ')}
                </p>
              </div>

              <span className="text-xs font-bold text-[#000000] bg-white px-3 py-1.5 rounded-lg border border-[#ccd5ae] shrink-0">
                Scheduled
              </span>
            </div>
          ))}
        </div>
      )}

      {/* ─── TAB: PREVIOUS ATTEMPTS ─────────────────────────────────────────── */}
      {activeTab === 'history' && (
        <div className="card bg-white border border-[#ccd5ae] overflow-hidden shadow-xs">
          {!testListData?.history || testListData.history.length === 0 ? (
            <div className="text-center py-12 text-[#333333]">
              <History className="w-8 h-8 mx-auto mb-2 text-[#333333]/40" />
              <p className="text-sm font-bold text-[#000000]">No test attempts recorded</p>
              <p className="text-xs text-[#333333] mt-1">Complete a weekly assessment to view your results here.</p>
            </div>
          ) : (
            <div className="divide-y divide-[#ccd5ae]">
              {testListData.history.map((att) => (
                <div key={att.attempt_id} className="p-4 sm:p-5 flex items-center justify-between gap-4">
                  <div className="space-y-1">
                    <h4 className="text-sm font-bold text-[#000000]">{att.title}</h4>
                    <p className="text-xs text-[#333333]">
                      Submitted on {new Date(att.started_at).toLocaleDateString()}
                    </p>
                  </div>

                  <div className="flex items-center gap-6">
                    <div className="text-right">
                      <div className="text-sm font-black text-[#000000]">
                        {att.score} / {att.max_score}
                      </div>
                      <div className="text-[11px] font-bold text-[#333333]">
                        {att.accuracy_pct}% Accuracy
                      </div>
                    </div>

                    <button
                      onClick={() => openAttemptReview(att.attempt_id)}
                      className="btn-secondary text-xs px-3 py-1.5 cursor-pointer"
                    >
                      View Review
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
