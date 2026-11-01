import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Flame, Star, Lightbulb, CheckCircle2, XCircle, ArrowRight, RotateCcw, AlertTriangle } from 'lucide-react'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { useI18n } from '@/i18n/I18nProvider'
import PageHeader from '@/components/PageHeader'
import LoadingSpinner from '@/components/LoadingSpinner'
import ErrorMessage from '@/components/ErrorMessage'

interface PracticeQuestion {
  id: string
  concept_id: string
  concept_name: string
  difficulty: number
  difficulty_label: 'easy' | 'medium' | 'hard'
  body: string
  options: string[]
  hints: string[]
}

interface PracticeAnswerResult {
  is_correct: boolean
  correct_index: number
  explanation: string
  error_type?: string
  new_p_know: number
  earned_xp: number
  current_streak: number
}

export default function StudentSolvePage() {
  const { t, lang } = useI18n()
  const user = useAuthStore((s) => s.user)
  const queryClient = useQueryClient()

  const [selectedOption, setSelectedOption] = useState<number | null>(null)
  const [revealedHints, setRevealedHints] = useState<number>(0)
  const [result, setResult] = useState<PracticeAnswerResult | null>(null)

  const searchParams = new URLSearchParams(window.location.search)
  const conceptIdFromUrl = searchParams.get('concept_id')

  // Fetch next adaptive question for this student
  const {
    data: qData,
    isLoading,
    isError,
    refetch,
  } = useQuery<{ question: PracticeQuestion; streak: number; xp: number }>({
    queryKey: ['practice-next-question', user?.id, lang, conceptIdFromUrl],
    queryFn: async () => {
      const url = conceptIdFromUrl
        ? `/students/${user?.id}/solve/next?lang=${lang}&concept_id=${conceptIdFromUrl}`
        : `/students/${user?.id}/solve/next?lang=${lang}`
      const res = await api.get(url)
      return res.data
    },
    enabled: !!user?.id,
  })

  // Submit answer mutation
  const submitAnswerMutation = useMutation({
    mutationFn: async (optionIdx: number) => {
      const res = await api.post(`/students/${user?.id}/solve/submit`, {
        question_id: qData?.question.id,
        selected_option: optionIdx,
        hints_used: revealedHints,
      })
      return res.data as PracticeAnswerResult
    },
    onSuccess: (data) => {
      setResult(data)
      queryClient.invalidateQueries({ queryKey: ['student-dashboard'] })
    },
  })

  const handleNext = () => {
    setSelectedOption(null)
    setRevealedHints(0)
    setResult(null)
    refetch()
  }

  if (isLoading) return <LoadingSpinner />
  if (isError || !qData) return <ErrorMessage onRetry={refetch} />

  const question = qData.question
  const difficultyBadge = {
    easy: 'bg-green-100 text-green-800 border-green-200',
    medium: 'bg-amber-100 text-amber-800 border-amber-200',
    hard: 'bg-purple-100 text-purple-800 border-purple-200',
  }[question.difficulty_label]

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <PageHeader
          title={`${t('nav_solve')}: ${question.concept_name}`}
          subtitle={t('solve_subtitle')}
        />
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 px-3 py-1 bg-amber-50 border border-amber-200 rounded-full text-xs font-semibold text-amber-800">
            <Star className="w-4 h-4 text-amber-500 fill-amber-500" />
            {result ? result.earned_xp : qData.xp} XP
          </span>
          <span className="flex items-center gap-1.5 px-3 py-1 bg-orange-50 border border-orange-200 rounded-full text-xs font-semibold text-orange-800">
            <Flame className="w-4 h-4 text-orange-500 fill-orange-500" />
            {result ? result.current_streak : qData.streak} {t('streak_days')}
          </span>
        </div>
      </div>

      {/* Question Card */}
      <div className="card p-6 bg-white border border-slate-200 rounded-xl shadow-sm space-y-5">
        <div className="flex items-center justify-between">
          <span className={`text-xs px-2.5 py-1 rounded-full font-semibold border ${difficultyBadge}`}>
            {t(`diff_${question.difficulty_label}`)}
          </span>
          <span className="text-xs text-slate-500 font-medium">
            {t('solve_adaptive_level')}
          </span>
        </div>

        <div className="text-base sm:text-lg font-semibold text-slate-900 leading-snug">
          {question.body}
        </div>

        {/* Options */}
        <div className="space-y-3 pt-2">
          {question.options.map((option, idx) => {
            let optionClass = 'bg-slate-50 border-slate-200 hover:bg-slate-100 text-slate-800'

            if (result) {
              if (idx === result.correct_index) {
                optionClass = 'bg-green-100 border-green-500 text-green-900 font-semibold'
              } else if (idx === selectedOption) {
                optionClass = 'bg-red-100 border-red-500 text-red-900'
              } else {
                optionClass = 'opacity-40 border-slate-200'
              }
            } else if (selectedOption === idx) {
              optionClass = 'border-primary-600 bg-primary-50 text-primary-900 font-medium'
            }

            return (
              <button
                key={idx}
                disabled={!!result || submitAnswerMutation.isPending}
                onClick={() => setSelectedOption(idx)}
                className={`w-full text-left p-4 rounded-xl border text-sm sm:text-base transition flex items-center justify-between ${optionClass}`}
              >
                <div className="flex items-center gap-3">
                  <span className="w-6 h-6 rounded-full border border-slate-300 flex items-center justify-center text-xs font-bold text-slate-600 shrink-0">
                    {String.fromCharCode(65 + idx)}
                  </span>
                  <span>{option}</span>
                </div>
                {result && idx === result.correct_index && (
                  <CheckCircle2 className="w-5 h-5 text-green-600 shrink-0" />
                )}
                {result && idx === selectedOption && !result.is_correct && (
                  <XCircle className="w-5 h-5 text-red-600 shrink-0" />
                )}
              </button>
            )
          })}
        </div>

        {/* Hints accordion */}
        {question.hints && question.hints.length > 0 && !result && (
          <div className="pt-2 border-t border-slate-100">
            {revealedHints < question.hints.length ? (
              <button
                onClick={() => setRevealedHints((h) => h + 1)}
                className="text-xs text-amber-700 hover:text-amber-800 font-medium flex items-center gap-1.5"
              >
                <Lightbulb className="w-3.5 h-3.5 text-amber-500" />
                {t('need_hint')} ({revealedHints}/{question.hints.length})
              </button>
            ) : null}

            {revealedHints > 0 && (
              <div className="mt-3 space-y-2">
                {question.hints.slice(0, revealedHints).map((hint, i) => (
                  <div key={i} className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-900 flex items-start gap-2">
                    <Lightbulb className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                    <span>{hint}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Result & Step-by-Step Explanation */}
        {result && (
          <div className={`p-4 rounded-xl border text-sm space-y-2 ${
            result.is_correct ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
          }`}>
            <div className="flex items-center gap-2 font-bold">
              {result.is_correct ? (
                <>
                  <CheckCircle2 className="w-5 h-5 text-green-600" />
                  <span className="text-green-900">{t('correct_answer_bravo')}</span>
                </>
              ) : (
                <>
                  <AlertTriangle className="w-5 h-5 text-red-600" />
                  <span className="text-red-900">{t('incorrect_answer_learn')}</span>
                </>
              )}
            </div>
            <p className="text-slate-700 leading-relaxed text-xs sm:text-sm">
              {result.explanation}
            </p>
            {result.error_type && (
              <span className="inline-block text-xs font-semibold px-2.5 py-0.5 bg-white border border-slate-200 text-slate-700 rounded-full mt-1">
                {t('identified_error_type')}: {t(`error_${result.error_type}`)}
              </span>
            )}
          </div>
        )}

        {/* Action Controls */}
        <div className="flex justify-between items-center pt-2">
          {!result ? (
            <button
              disabled={selectedOption === null || submitAnswerMutation.isPending}
              onClick={() => selectedOption !== null && submitAnswerMutation.mutate(selectedOption)}
              className="btn-primary ml-auto px-6 py-2.5 rounded-lg text-sm font-semibold"
            >
              {submitAnswerMutation.isPending ? t('checking_answer') : t('check_answer')}
            </button>
          ) : (
            <div className="flex w-full justify-between items-center">
              <a
                href={`/student/learn?concept_id=${question.concept_id}`}
                className="text-xs text-primary-700 font-medium hover:underline flex items-center gap-1"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                {t('review_micro_lesson')}
              </a>
              <button
                onClick={handleNext}
                className="btn-primary px-6 py-2.5 rounded-lg text-sm font-semibold inline-flex items-center gap-2"
              >
                <span>{t('next_challenge')}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
