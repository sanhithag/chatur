import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { BookOpen, Lightbulb, Eye, Compass, HelpCircle, CheckCircle, Volume2, ArrowRight, GitFork } from 'lucide-react'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { useI18n } from '@/i18n/I18nProvider'
import PageHeader from '@/components/PageHeader'
import LoadingSpinner from '@/components/LoadingSpinner'
import ErrorMessage from '@/components/ErrorMessage'

type ExplanationStyle = 'simple' | 'detailed' | 'visual' | 'analogy' | 'worked_example'

interface LessonContent {
  concept_id: string
  concept_name: string
  grade: number
  subject_name: string
  working_level_name?: string
  is_foundation_path: boolean
  key_terms: string[]
  styles: Record<ExplanationStyle, { title: string; content: string }>
  comprehension_check: {
    question: string
    options: string[]
    correct_index: number
    explanation: string
  }
}

export default function StudentLearnPage() {
  const { t, lang } = useI18n()
  const user = useAuthStore((s) => s.user)
  const [selectedStyle, setSelectedStyle] = useState<ExplanationStyle>('simple')
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null)
  const [hasAnswered, setHasAnswered] = useState(false)
  const [speechActive, setSpeechActive] = useState(false)

  const searchParams = new URLSearchParams(window.location.search)
  const conceptIdFromUrl = searchParams.get('concept_id')

  // Fetch student active learning concept
  const { data: lesson, isLoading, isError, refetch } = useQuery<LessonContent>({
    queryKey: ['student-active-lesson', user?.id, lang, conceptIdFromUrl],
    queryFn: async () => {
      const url = conceptIdFromUrl
        ? `/students/${user?.id}/learn/active?lang=${lang}&concept_id=${conceptIdFromUrl}`
        : `/students/${user?.id}/learn/active?lang=${lang}`
      const res = await api.get(url)
      return res.data
    },
    enabled: !!user?.id,
  })

  // Fetch prerequisite DAG chain for this concept
  const { data: chainData } = useQuery<{
    target_concept_id: string
    target_concept_name: string
    chain: Array<{
      id: string
      code: string
      name_en: string
      grade: number
      p_know: number
      level_name: string
      is_mastered: boolean
    }>
  }>({
    queryKey: ['student-concept-chain', user?.id, lesson?.concept_id],
    queryFn: async () => {
      const res = await api.get(`/students/${user?.id}/concepts/${lesson?.concept_id}/chain`)
      return res.data
    },
    enabled: !!user?.id && !!lesson?.concept_id,
  })

  const styleIcons: Record<ExplanationStyle, React.ReactNode> = {
    simple: <BookOpen className="w-4 h-4" />,
    detailed: <Compass className="w-4 h-4" />,
    visual: <Eye className="w-4 h-4" />,
    analogy: <Lightbulb className="w-4 h-4" />,
    worked_example: <HelpCircle className="w-4 h-4" />,
  }

  const styleLabels: Record<ExplanationStyle, string> = {
    simple: t('style_simple'),
    detailed: t('style_detailed'),
    visual: t('style_visual'),
    analogy: t('style_analogy'),
    worked_example: t('style_worked_example'),
  }

  const toggleSpeech = (text: string) => {
    if (!('speechSynthesis' in window)) return
    if (speechActive) {
      window.speechSynthesis.cancel()
      setSpeechActive(false)
    } else {
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = lang === 'te' ? 'te-IN' : lang === 'hi' ? 'hi-IN' : 'en-IN'
      utterance.onend = () => setSpeechActive(false)
      window.speechSynthesis.speak(utterance)
      setSpeechActive(true)
    }
  }

  if (isLoading) return <LoadingSpinner />
  if (isError || !lesson) return <ErrorMessage onRetry={refetch} />

  const currentExplanation = lesson.styles[selectedStyle] || lesson.styles.simple

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <PageHeader
        title={`${t('nav_learn')}: ${lesson.concept_name}`}
        subtitle={`${lesson.subject_name} · ${t('grade_level')} ${lesson.grade}`}
      />

      {/* Foundation Path banner if student is repairing a prerequisite */}
      {lesson.is_foundation_path && (
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl flex items-start gap-3">
          <Compass className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-semibold text-amber-900">{t('foundation_path_active')}</h4>
            <p className="text-xs text-amber-700 mt-0.5">
              {t('foundation_path_explainer')} ({lesson.working_level_name})
            </p>
          </div>
        </div>
      )}

      {/* Prerequisite Knowledge Graph Chain */}
      {chainData && chainData.chain && chainData.chain.length > 1 && (
        <div className="card p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
            <span className="flex items-center gap-1.5">
              <GitFork className="w-4 h-4 text-primary-600" />
              Prerequisite Learning Pathway (Cross-Grade DAG)
            </span>
            <span className="text-slate-500 font-normal hidden sm:inline">
              Traced to Class {chainData.chain[0].grade} foundational prerequisites
            </span>
          </div>
          <div className="flex items-center gap-2 overflow-x-auto py-2">
            {chainData.chain.map((node, i) => (
              <div key={node.id} className="flex items-center gap-2 shrink-0">
                <a
                  href={`/student/learn?concept_id=${node.id}`}
                  className={`p-2.5 rounded-lg border text-xs flex flex-col gap-0.5 transition-all hover:shadow-sm ${
                    node.id === lesson.concept_id
                      ? 'bg-primary-50 border-primary-500 font-bold text-primary-950 ring-2 ring-primary-300'
                      : node.is_mastered
                      ? 'bg-green-50 border-green-200 text-green-900'
                      : 'bg-white border-slate-200 text-slate-700 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                      Class {node.grade}
                    </span>
                    {node.is_mastered ? (
                      <span className="text-[10px] text-green-700 font-semibold">Mastered</span>
                    ) : (
                      <span className="text-[10px] text-amber-700 font-semibold">{Math.round(node.p_know * 100)}%</span>
                    )}
                  </div>
                  <span className="text-xs mt-0.5">{node.name_en}</span>
                </a>
                {i < chainData.chain.length - 1 && (
                  <ArrowRight className="w-4 h-4 text-slate-400 shrink-0" />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Explanation Style Selector Tabs */}
      <div className="card p-2 flex flex-wrap gap-2 bg-slate-50 border border-slate-200 rounded-xl">
        {(['simple', 'detailed', 'visual', 'analogy', 'worked_example'] as ExplanationStyle[]).map((style) => (
          <button
            key={style}
            onClick={() => setSelectedStyle(style)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs sm:text-sm font-medium transition-all ${
              selectedStyle === style
                ? 'bg-primary-800 text-white shadow-sm'
                : 'text-slate-600 hover:bg-slate-200'
            }`}
          >
            {styleIcons[style]}
            {styleLabels[style]}
          </button>
        ))}
      </div>

      {/* Main Micro-Lesson Card */}
      <div className="card p-6 space-y-5 bg-white border border-slate-200 rounded-xl shadow-sm">
        <div className="flex items-center justify-between border-b pb-3">
          <h2 className="text-lg font-bold text-slate-900">{currentExplanation.title}</h2>
          <button
            onClick={() => toggleSpeech(currentExplanation.content)}
            className={`p-2 rounded-lg border text-xs flex items-center gap-1.5 transition ${
              speechActive ? 'bg-primary-100 text-primary-800 border-primary-300' : 'bg-slate-50 text-slate-600 hover:bg-slate-100'
            }`}
            title="Read aloud"
          >
            <Volume2 className="w-4 h-4" />
            <span>{speechActive ? t('stop_audio') : t('listen')}</span>
          </button>
        </div>

        {/* Lesson Body */}
        <div className="prose prose-slate max-w-none text-slate-800 leading-relaxed whitespace-pre-line text-sm sm:text-base">
          {currentExplanation.content}
        </div>

        {/* Key Terminology Badges */}
        {lesson.key_terms && lesson.key_terms.length > 0 && (
          <div className="pt-4 border-t border-slate-100">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-2">
              {t('key_terminology')}
            </span>
            <div className="flex flex-wrap gap-2">
              {lesson.key_terms.map((term, i) => (
                <span key={i} className="px-2.5 py-1 bg-slate-100 text-slate-700 text-xs rounded-full font-medium">
                  {term}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Quick Comprehension Check */}
      <div className="card p-6 bg-slate-50 border border-slate-200 rounded-xl space-y-4">
        <div className="flex items-center gap-2">
          <HelpCircle className="w-5 h-5 text-primary-600" />
          <h3 className="font-semibold text-slate-900 text-base">{t('quick_check')}</h3>
        </div>
        <p className="text-sm text-slate-700 font-medium">{lesson.comprehension_check.question}</p>

        <div className="space-y-2">
          {lesson.comprehension_check.options.map((option, idx) => {
            let btnStyle = 'bg-white border-slate-200 text-slate-800 hover:bg-slate-100'
            if (hasAnswered) {
              if (idx === lesson.comprehension_check.correct_index) {
                btnStyle = 'bg-green-100 border-green-500 text-green-900 font-medium'
              } else if (idx === selectedAnswer) {
                btnStyle = 'bg-red-100 border-red-500 text-red-900'
              } else {
                btnStyle = 'opacity-50 border-slate-200'
              }
            }

            return (
              <button
                key={idx}
                disabled={hasAnswered}
                onClick={() => {
                  setSelectedAnswer(idx)
                  setHasAnswered(true)
                }}
                className={`w-full text-left p-3 rounded-lg border text-sm transition flex items-center justify-between ${btnStyle}`}
              >
                <span>{option}</span>
                {hasAnswered && idx === lesson.comprehension_check.correct_index && (
                  <CheckCircle className="w-4 h-4 text-green-600 shrink-0" />
                )}
              </button>
            )
          })}
        </div>

        {hasAnswered && (
          <div className="p-3 bg-white rounded-lg border text-xs space-y-1">
            <span className="font-bold text-slate-800">{t('explanation')}:</span>
            <p className="text-slate-600">{lesson.comprehension_check.explanation}</p>
          </div>
        )}
      </div>

      {/* Next Step Action */}
      <div className="flex justify-end gap-3 pt-2">
        <a
          href={`/student/solve?concept_id=${lesson.concept_id}`}
          className="btn-primary inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold"
        >
          <span>{t('ready_to_solve')}</span>
          <ArrowRight className="w-4 h-4" />
        </a>
      </div>
    </div>
  )
}
