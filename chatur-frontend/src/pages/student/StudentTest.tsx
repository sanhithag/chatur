import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { CheckCircle2, AlertCircle, Printer, ArrowRight, ArrowLeft, Send, Sparkles } from 'lucide-react'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { useI18n } from '@/i18n/I18nProvider'
import PageHeader from '@/components/PageHeader'
import LoadingSpinner from '@/components/LoadingSpinner'
import ErrorMessage from '@/components/ErrorMessage'

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
  score: number
  max_score: number
  accuracy_pct: number
  feedback_message: string
  prerequisite_diagnosed?: string
  proposal_sent_to_teacher: boolean
}

export default function StudentTestPage() {
  const { t, lang } = useI18n()
  const user = useAuthStore((s) => s.user)
  const queryClient = useQueryClient()

  const [currentIndex, setCurrentIndex] = useState(0)
  const [answers, setAnswers] = useState<Record<string, number>>({})
  const [testResult, setTestResult] = useState<TestSubmitResult | null>(null)

  // Fetch or generate weekly adaptive test paper
  const {
    data: paper,
    isLoading,
    isError,
    refetch,
  } = useQuery<TestPaper>({
    queryKey: ['student-test-paper', user?.id, lang],
    queryFn: async () => {
      const res = await api.get(`/students/${user?.id}/test/active?lang=${lang}`)
      return res.data
    },
    enabled: !!user?.id,
  })

  // Submit test mutation
  const submitTestMutation = useMutation({
    mutationFn: async () => {
      const formattedResponses = Object.entries(answers).map(([qId, optIdx]) => ({
        question_id: qId,
        selected_option: optIdx,
      }))
      const res = await api.post(`/students/${user?.id}/test/submit`, {
        assessment_id: paper?.assessment_id,
        responses: formattedResponses,
      })
      return res.data as TestSubmitResult
    },
    onSuccess: (data) => {
      setTestResult(data)
      queryClient.invalidateQueries({ queryKey: ['student-dashboard'] })
    },
  })

  if (isLoading) return <LoadingSpinner />
  if (isError || !paper) return <ErrorMessage onRetry={refetch} />

  // Render Completed / Results view
  if (testResult) {
    return (
      <div className="p-6 max-w-2xl mx-auto space-y-6">
        <div className="card p-8 bg-white border border-slate-200 rounded-2xl shadow-sm text-center space-y-5">
          <div className="w-16 h-16 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center mx-auto">
            <Sparkles className="w-8 h-8" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900">{t('test_completed_title')}</h2>
          <div className="text-4xl font-extrabold text-primary-800">
            {testResult.score} / {testResult.max_score}
            <span className="text-lg font-normal text-slate-500 block mt-1">
              ({testResult.accuracy_pct}%)
            </span>
          </div>
          <p className="text-slate-600 text-sm max-w-md mx-auto">{testResult.feedback_message}</p>

          {testResult.proposal_sent_to_teacher && (
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-xl text-left text-xs text-blue-900 space-y-1">
              <span className="font-bold flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-blue-600" />
                {t('evidence_sent_to_teacher')}
              </span>
              <p className="text-blue-700">{t('teacher_review_notice')}</p>
            </div>
          )}

          <div className="pt-4 flex justify-center gap-3">
            <a href="/student/dashboard" className="btn-secondary px-6 py-2.5 rounded-lg text-sm font-semibold">
              {t('nav_dashboard')}
            </a>
            <a href="/student/solve" className="btn-primary px-6 py-2.5 rounded-lg text-sm font-semibold">
              {t('nav_solve')}
            </a>
          </div>
        </div>
      </div>
    )
  }

  const currentItem = paper.items[currentIndex]
  const isAnswered = answers[currentItem.question_id] !== undefined
  const answeredCount = Object.keys(answers).length
  const isLastQuestion = currentIndex === paper.items.length - 1

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <PageHeader title={paper.title} subtitle={`${paper.total_questions} ${t('questions_total')}`} />
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => window.print()}
            className="p-2 border border-slate-300 rounded-lg text-xs font-medium text-slate-700 bg-white hover:bg-slate-50 flex items-center gap-1.5"
            title="Print paper assessment"
          >
            <Printer className="w-4 h-4" />
            <span>{t('print')}</span>
          </button>
        </div>
      </div>

      {/* Progress & Stepper */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs text-slate-500 font-medium">
          <span>
            {t('question')} {currentIndex + 1} {t('of')} {paper.items.length}
          </span>
          <span>
            {answeredCount}/{paper.items.length} {t('answered')}
          </span>
        </div>
        <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
          <div
            className="bg-primary-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${((currentIndex + 1) / paper.items.length) * 100}%` }}
          />
        </div>
      </div>

      {/* Question Card */}
      <div className="card p-6 bg-white border border-slate-200 rounded-xl shadow-sm space-y-6">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold px-2.5 py-1 bg-slate-100 text-slate-700 rounded-full border border-slate-200">
            {currentItem.concept_name}
          </span>
          <span className="text-xs text-slate-400 font-medium">
            {currentItem.section_type === 'prereq_probe' && `🔍 ${t('prereq_probe')}`}
            {currentItem.section_type === 'working_level' && `🎯 ${t('working_level')}`}
            {currentItem.section_type === 'stretch' && `🚀 ${t('stretch_question')}`}
          </span>
        </div>

        <div className="text-base sm:text-lg font-semibold text-slate-900 leading-snug">
          {currentItem.question_text}
        </div>

        {/* Options */}
        <div className="space-y-3">
          {currentItem.options.map((opt, idx) => {
            const isSelected = answers[currentItem.question_id] === idx
            return (
              <button
                key={idx}
                onClick={() => setAnswers({ ...answers, [currentItem.question_id]: idx })}
                className={`w-full text-left p-4 rounded-xl border text-sm sm:text-base transition flex items-center gap-3 ${
                  isSelected
                    ? 'border-primary-700 bg-primary-50 text-primary-950 font-semibold shadow-sm'
                    : 'border-slate-200 hover:bg-slate-50 text-slate-800'
                }`}
              >
                <span
                  className={`w-6 h-6 rounded-full border flex items-center justify-center text-xs font-bold shrink-0 ${
                    isSelected ? 'border-primary-700 bg-primary-800 text-white' : 'border-slate-300 text-slate-600'
                  }`}
                >
                  {String.fromCharCode(65 + idx)}
                </span>
                <span>{opt}</span>
              </button>
            )
          })}
        </div>

        {/* Navigation Buttons */}
        <div className="flex justify-between items-center pt-4 border-t border-slate-100">
          <button
            disabled={currentIndex === 0}
            onClick={() => setCurrentIndex((i) => i - 1)}
            className="btn-secondary px-4 py-2 rounded-lg text-sm font-medium inline-flex items-center gap-1.5 disabled:opacity-40"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>{t('previous')}</span>
          </button>

          {!isLastQuestion ? (
            <button
              onClick={() => setCurrentIndex((i) => i + 1)}
              className="btn-primary px-5 py-2 rounded-lg text-sm font-semibold inline-flex items-center gap-1.5"
            >
              <span>{t('next')}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              disabled={answeredCount === 0 || submitTestMutation.isPending}
              onClick={() => submitTestMutation.mutate()}
              className="btn-primary bg-green-700 hover:bg-green-800 px-6 py-2.5 rounded-lg text-sm font-bold inline-flex items-center gap-2"
            >
              <Send className="w-4 h-4" />
              <span>{submitTestMutation.isPending ? t('submitting') : t('submit_assessment')}</span>
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
