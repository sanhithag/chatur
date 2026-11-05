import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams, useNavigate } from 'react-router-dom'
import {
  BookOpen,
  Lightbulb,
  Eye,
  Compass,
  HelpCircle,
  CheckCircle,
  Volume2,
  VolumeX,
  ArrowRight,
  ArrowLeft,
  Target,
  ChevronRight,
  ChevronDown,
  Check,
  AlertCircle,
  Plus,
  CheckSquare,
} from 'lucide-react'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { useI18n } from '@/i18n/I18nProvider'
import LoadingSpinner from '@/components/LoadingSpinner'
import ErrorMessage from '@/components/ErrorMessage'

type ExplanationStyle = 'simple' | 'detailed' | 'visual' | 'analogy' | 'worked_example'

interface LessonContent {
  concept_id: string
  concept_name: string
  grade: number
  subject_name: string
  subject_id?: string
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
  lesson_source?: 'stored' | 'legacy' | 'pending'
  language_served?: string
  translation_fallback?: boolean
  extra?: {
    introduction?: string
    objectives?: string[]
    summary?: string
    definitions?: { term: string; meaning: string }[]
    formulas?: { name: string; formula: string; description: string }[]
    misconceptions?: { wrong: string; correct: string }[]
  } | null
  prerequisites?: Array<{
    id: string
    code: string
    name: string
    grade: number
    is_strict: boolean
  }>
  related_concepts?: Array<{
    id: string
    name: string
    difficulty: string
    grade: number
  }>
}

interface CurriculumSubjectItem {
  id: string
  code: string
  name_en: string
  name_te?: string
  name_hi?: string
  domain: string
}

interface CurriculumNavigator {
  grades: number[]
  grade: number
  chapters: Array<{
    id: string
    chapter_no: number
    unit: string
    name_en: string
    name_te?: string
    name_hi?: string
    concepts: Array<{
      id: string
      name_en: string
      name_te?: string
      name_hi?: string
      lesson_ready: boolean
    }>
  }>
}

export default function StudentLearn() {
  const { t, lang } = useI18n()
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const [searchParams, setSearchParams] = useSearchParams()

  const [selectedStyle, setSelectedStyle] = useState<ExplanationStyle>('simple')
  const [speechActive, setSpeechActive] = useState(false)
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null)
  const [hasAnswered, setHasAnswered] = useState(false)
  const [openChapters, setOpenChapters] = useState<Record<string, boolean>>({})
  const [activeGrade, setActiveGrade] = useState<number>(10)
  const [activeSubjectId, setActiveSubjectId] = useState<string | null>(null)
  const [activeConceptId, setActiveConceptId] = useState<string | null>(null)
  const [taskAdded, setTaskAdded] = useState(false)

  // Fetch available subjects
  const { data: subjects } = useQuery<CurriculumSubjectItem[]>({
    queryKey: ['curriculum-subjects'],
    queryFn: async () => {
      const res = await api.get('/curriculum/subjects')
      return res.data
    },
  })

  // Initialize active subject
  useEffect(() => {
    const urlSubj = searchParams.get('subject_id')
    const storedSubj = localStorage.getItem('chatur_subject')
    if (urlSubj) {
      setActiveSubjectId(urlSubj)
    } else if (storedSubj) {
      setActiveSubjectId(storedSubj)
    } else if (subjects && subjects.length > 0) {
      setActiveSubjectId(subjects[0].id)
    }
  }, [subjects, searchParams])

  // Initialize active concept
  useEffect(() => {
    const urlConcept = searchParams.get('concept_id')
    if (urlConcept) {
      setActiveConceptId(urlConcept)
    }
  }, [searchParams])

  // Fetch subject-specific chapter navigator
  const { data: navigatorData } = useQuery<CurriculumNavigator>({
    queryKey: ['curriculum-navigator', activeSubjectId, activeGrade],
    queryFn: async () => {
      if (!activeSubjectId) return null
      const res = await api.get(`/curriculum/subjects/${activeSubjectId}/navigator`, {
        params: { grade: activeGrade },
      })
      return res.data
    },
    enabled: !!activeSubjectId,
  })

  // Expand chapter when concept is active
  useEffect(() => {
    if (navigatorData?.chapters) {
      const initialOpen: Record<string, boolean> = {}
      navigatorData.chapters.forEach((ch, idx) => {
        const containsActive = ch.concepts.some((c) => c.id === activeConceptId)
        initialOpen[ch.id] = containsActive || idx === 0
      })
      setOpenChapters(initialOpen)
    }
  }, [navigatorData, activeConceptId])

  // Fetch active lesson content
  const { data: lesson, isLoading, isError, refetch } = useQuery<LessonContent>({
    queryKey: ['student-learn-active', user?.id, activeConceptId, activeSubjectId, lang],
    queryFn: async () => {
      const params: Record<string, string> = { lang }
      if (activeConceptId) params.concept_id = activeConceptId
      if (activeSubjectId) params.subject_id = activeSubjectId

      const res = await api.get(`/students/${user?.id}/learn/active`, { params })
      if (res.data?.concept_id) {
        localStorage.setItem(
          'chatur_last_concept',
          JSON.stringify({ id: res.data.concept_id, name: res.data.concept_name })
        )
      }
      return res.data
    },
    enabled: !!user?.id,
  })

  const styleIcons: Record<ExplanationStyle, React.ReactNode> = {
    simple: <BookOpen className="w-4 h-4 text-[#000000]" />,
    detailed: <Compass className="w-4 h-4 text-[#000000]" />,
    visual: <Eye className="w-4 h-4 text-[#000000]" />,
    analogy: <Lightbulb className="w-4 h-4 text-[#000000]" />,
    worked_example: <HelpCircle className="w-4 h-4 text-[#000000]" />,
  }

  const styleLabels: Record<ExplanationStyle, string> = {
    simple: 'Simple',
    detailed: 'Detailed',
    visual: 'Visual Diagram',
    analogy: 'Analogy',
    worked_example: 'Worked Example',
  }

  const toggleSpeech = (text: string) => {
    if (!('speechSynthesis' in window)) return
    if (speechActive) {
      window.speechSynthesis.cancel()
      setSpeechActive(false)
    } else {
      const utterance = new SpeechSynthesisUtterance(text.replace(/[#*`_]/g, ''))
      utterance.lang = lang === 'te' ? 'te-IN' : lang === 'hi' ? 'hi-IN' : 'en-IN'
      utterance.onend = () => setSpeechActive(false)
      window.speechSynthesis.speak(utterance)
      setSpeechActive(true)
    }
  }

  const selectConcept = (conceptId: string) => {
    setActiveConceptId(conceptId)
    setSearchParams({ concept_id: conceptId, ...(activeSubjectId ? { subject_id: activeSubjectId } : {}) })
    setSelectedAnswer(null)
    setHasAnswered(false)
    setTaskAdded(false)
  }

  const selectSubject = (subjId: string) => {
    setActiveSubjectId(subjId)
    localStorage.setItem('chatur_subject', subjId)
    setActiveConceptId(null)
    setSearchParams({ subject_id: subjId })
  }

  const toggleChapterAccordion = (chId: string) => {
    setOpenChapters((prev) => ({ ...prev, [chId]: !prev[chId] }))
  }

  const handleAddLessonToTodo = async () => {
    if (!lesson || !user?.id) return
    try {
      await api.post(`/students/${user.id}/tasks`, {
        title: `Study: ${lesson.concept_name}`,
        task_type: 'lesson',
        link_type: 'concept',
        link_id: lesson.concept_id,
      })
      setTaskAdded(true)
    } catch (err) {
      console.error('Failed to add task to todo:', err)
    }
  }

  const loc = (o: { name_en: string; name_te?: string; name_hi?: string }) =>
    (lang === 'te' && o.name_te) || (lang === 'hi' && o.name_hi) || o.name_en

  if (isLoading) return <LoadingSpinner />
  if (isError || !lesson) return <ErrorMessage onRetry={refetch} />

  const currentExplanation = lesson.styles[selectedStyle] || lesson.styles.simple

  // Collect all concepts across chapters for previous / next navigation
  const allNavConcepts = navigatorData?.chapters?.flatMap((ch) => ch.concepts) ?? []
  const currentIdx = allNavConcepts.findIndex((c) => c.id === lesson.concept_id)
  const prevConcept = currentIdx > 0 ? allNavConcepts[currentIdx - 1] : null
  const nextConcept = currentIdx >= 0 && currentIdx < allNavConcepts.length - 1 ? allNavConcepts[currentIdx + 1] : null

  return (
    <div className="flex flex-col lg:flex-row h-full min-h-[calc(100vh-3.5rem)] text-[#000000]">
      {/* GeeksforGeeks-Style Left Curriculum Sidebar */}
      <aside className="w-full lg:w-72 bg-[#faedcd]/40 border-r border-[#ccd5ae] shrink-0 flex flex-col max-h-[calc(100vh-3.5rem)] overflow-y-auto text-[#000000]">
        {/* Subject & Grade Selection */}
        <div className="p-3 border-b border-[#ccd5ae] bg-white space-y-2.5">
          <div className="text-[10px] font-bold uppercase tracking-wider text-[#333333] flex items-center justify-between">
            <span>Subject & Class</span>
            {navigatorData?.grades && (
              <div className="flex items-center gap-1">
                {navigatorData.grades.map((g) => (
                  <button
                    key={g}
                    onClick={() => setActiveGrade(g)}
                    className={`px-1.5 py-0.5 rounded text-[10px] font-bold transition-all cursor-pointer ${
                      activeGrade === g
                        ? 'bg-[#ccd5ae] text-[#000000] border border-[#ccd5ae]'
                        : 'bg-white border border-[#ccd5ae] text-[#333333] hover:bg-[#e9edc9]'
                    }`}
                  >
                    Cl {g}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="flex flex-wrap gap-1">
            {subjects?.map((s) => (
              <button
                key={s.id}
                onClick={() => selectSubject(s.id)}
                className={`px-2 py-1 rounded text-xs font-semibold transition-all cursor-pointer ${
                  activeSubjectId === s.id
                    ? 'bg-[#ccd5ae] text-[#000000] border border-[#ccd5ae] shadow-2xs'
                    : 'bg-white border border-[#ccd5ae] text-[#333333] hover:bg-[#e9edc9]'
                }`}
              >
                {loc(s)}
              </button>
            ))}
          </div>
        </div>

        {/* Chapters & Topics Accordion Tree */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1 divide-y divide-[#ccd5ae]/40 text-xs">
          <div className="px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-[#333333]">
            Curriculum Hierarchy
          </div>
          {navigatorData?.chapters?.map((ch) => {
            const isOpen = !!openChapters[ch.id]
            const isChActive = ch.concepts.some((c) => c.id === lesson.concept_id)

            return (
              <div key={ch.id} className="pt-1">
                <button
                  onClick={() => toggleChapterAccordion(ch.id)}
                  className={`w-full text-left px-2 py-1.5 rounded flex items-center justify-between text-xs font-semibold transition-colors cursor-pointer ${
                    isChActive
                      ? 'bg-[#e9edc9] text-[#000000] border border-[#ccd5ae]'
                      : 'text-[#000000] hover:bg-[#e9edc9]/50'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate pr-2">
                    <span className="w-4 h-4 rounded bg-[#faedcd] text-[#000000] font-bold text-[10px] flex items-center justify-center shrink-0 border border-[#ccd5ae]">
                      {ch.chapter_no}
                    </span>
                    <span className="truncate">{loc(ch)}</span>
                  </div>
                  {isOpen ? (
                    <ChevronDown className="w-3.5 h-3.5 text-[#333333] shrink-0" />
                  ) : (
                    <ChevronRight className="w-3.5 h-3.5 text-[#333333] shrink-0" />
                  )}
                </button>

                {isOpen && (
                  <div className="pl-5 pr-1 py-1 space-y-0.5 border-l border-[#ccd5ae] ml-3 mt-0.5">
                    {ch.concepts.map((c) => {
                      const isCurrent = c.id === lesson.concept_id
                      return (
                        <button
                          key={c.id}
                          onClick={() => selectConcept(c.id)}
                          className={`w-full text-left px-2 py-1 rounded text-xs flex items-center justify-between transition-all cursor-pointer ${
                            isCurrent
                              ? 'bg-[#ccd5ae] text-[#000000] font-bold shadow-2xs'
                              : 'text-[#333333] hover:text-[#000000] hover:bg-[#e9edc9]/60'
                          }`}
                        >
                          <span className="truncate">{loc(c)}</span>
                          {isCurrent && <Check className="w-3.5 h-3.5 text-[#000000] shrink-0 ml-1" />}
                        </button>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Practice & To-do Quick Action Widget */}
        <div className="p-3 border-t border-[#ccd5ae] bg-white space-y-2">
          <button
            onClick={() => navigate(`/student/practice?concept_id=${lesson.concept_id}`)}
            className="w-full btn-primary text-xs py-1.5 flex items-center justify-center gap-1.5"
          >
            <Target className="w-3.5 h-3.5" />
            Practise This Topic
          </button>
          <button
            onClick={handleAddLessonToTodo}
            disabled={taskAdded}
            className="w-full btn-secondary text-xs py-1.5 flex items-center justify-center gap-1.5"
          >
            {taskAdded ? <CheckSquare className="w-3.5 h-3.5 text-emerald-800" /> : <Plus className="w-3.5 h-3.5" />}
            {taskAdded ? 'Added to To-Do' : 'Add to To-Do List'}
          </button>
        </div>
      </aside>

      {/* Main Content Workspace (GeeksforGeeks Structured Reading Experience) */}
      <div className="flex-1 overflow-y-auto p-4 lg:p-6 space-y-5 bg-[#fefae0] text-[#000000]">
        {/* Breadcrumb Hierarchy */}
        <div className="flex items-center gap-1.5 text-xs text-[#333333] flex-wrap">
          <span>CBSE</span>
          <ChevronRight className="w-3 h-3 text-[#333333]" />
          <span>Class {lesson.grade}</span>
          <ChevronRight className="w-3 h-3 text-[#333333]" />
          <span className="font-semibold text-[#000000]">{lesson.subject_name}</span>
          <ChevronRight className="w-3 h-3 text-[#333333]" />
          <span className="font-bold text-[#000000] truncate">
            {lesson.concept_name}
          </span>
        </div>

        {/* Top Concept Banner: Sand background with Sage border */}
        <div className="bg-[#faedcd] border border-[#ccd5ae] rounded-lg p-5 text-[#000000] shadow-xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-[#e9edc9] text-[#000000] border border-[#ccd5ae]">
                  Class {lesson.grade} &bull; {lesson.subject_name}
                </span>
                {lesson.translation_fallback && (
                  <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-white text-[#333333] border border-[#ccd5ae]">
                    English Original
                  </span>
                )}
              </div>
              <h1 className="text-xl sm:text-2xl font-bold text-[#000000] tracking-tight">
                {lesson.concept_name}
              </h1>
              {lesson.extra?.introduction && (
                <p className="text-xs sm:text-sm text-[#333333] max-w-3xl leading-relaxed">
                  {lesson.extra.introduction}
                </p>
              )}
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <button
                onClick={() => toggleSpeech(currentExplanation.content)}
                className="btn-secondary text-xs py-1.5 px-3 flex items-center gap-1.5"
                title="Audio voice explanation"
              >
                {speechActive ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
                <span>{speechActive ? 'Stop' : 'Listen'}</span>
              </button>

              <button
                onClick={() => navigate(`/student/practice?concept_id=${lesson.concept_id}`)}
                className="btn-primary text-xs py-1.5 px-3.5"
              >
                <Target className="w-3.5 h-3.5" />
                Practise
              </button>
            </div>
          </div>
        </div>

        {/* Learning Objectives */}
        {lesson.extra?.objectives && lesson.extra.objectives.length > 0 && (
          <div className="card p-4 bg-white border border-[#ccd5ae]">
            <h3 className="text-xs font-bold uppercase tracking-wider text-[#333333] mb-2">
              Learning Objectives
            </h3>
            <ul className="space-y-1 text-xs text-[#000000]">
              {lesson.extra.objectives.map((obj, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-[#d4a373] font-bold">&bull;</span>
                  <span>{obj}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Explanation Style Tabs */}
        <div className="flex flex-wrap gap-1.5 p-1 bg-[#faedcd]/40 border border-[#ccd5ae] rounded-lg text-xs">
          {(['simple', 'detailed', 'visual', 'analogy', 'worked_example'] as ExplanationStyle[]).map((style) => (
            <button
              key={style}
              onClick={() => setSelectedStyle(style)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-semibold transition-all cursor-pointer ${
                selectedStyle === style
                  ? 'bg-[#d4a373] text-[#000000] border border-[#ccd5ae] shadow-2xs'
                  : 'bg-white border border-[#ccd5ae] text-[#333333] hover:bg-[#e9edc9]'
              }`}
            >
              {styleIcons[style]}
              <span>{styleLabels[style]}</span>
            </button>
          ))}
        </div>

        {/* Active Explanation Reading Area */}
        <div className="card p-5 bg-white border border-[#ccd5ae] space-y-3 text-[#000000]">
          <div className="border-b border-[#ccd5ae] pb-2 flex items-center justify-between">
            <h2 className="text-base font-bold text-[#000000]">{currentExplanation.title}</h2>
            <span className="text-[11px] text-[#333333] uppercase">
              Mode: {styleLabels[selectedStyle]}
            </span>
          </div>
          <div className="prose max-w-none text-xs sm:text-sm text-[#000000] leading-relaxed whitespace-pre-line">
            {currentExplanation.content}
          </div>
        </div>

        {/* Important Formulas & Laws */}
        {lesson.extra?.formulas && lesson.extra.formulas.length > 0 && (
          <div className="card p-4 bg-white border border-[#ccd5ae] space-y-2.5">
            <h3 className="text-xs font-bold uppercase tracking-wider text-[#333333]">
              Formulas & Mathematical Rules
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs">
              {lesson.extra.formulas.map((f, i) => (
                <div key={i} className="p-3 rounded border border-[#ccd5ae] bg-[#faedcd]/20 space-y-1">
                  <div className="font-bold text-[#000000]">{f.name}</div>
                  <div className="p-2 rounded bg-white font-mono font-bold text-[#000000] border border-[#ccd5ae]">
                    {f.formula}
                  </div>
                  <div className="text-[11px] text-[#333333]">{f.description}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Definitions & Terminology */}
        {lesson.extra?.definitions && lesson.extra.definitions.length > 0 && (
          <div className="card p-4 bg-white border border-[#ccd5ae] space-y-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-[#333333]">
              Key Terminology & Definitions
            </h3>
            <div className="divide-y divide-[#ccd5ae]/40 text-xs">
              {lesson.extra.definitions.map((d, i) => (
                <div key={i} className="py-2 flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-4">
                  <span className="font-bold text-[#000000] min-w-[130px] shrink-0">{d.term}</span>
                  <span className="text-[#333333]">{d.meaning}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Comprehension Check */}
        <div className="card p-5 bg-white border border-[#ccd5ae] space-y-3 text-[#000000]">
          <div className="flex items-center justify-between border-b border-[#ccd5ae] pb-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-[#000000]">
              Concept Check
            </h3>
            <span className="text-[11px] text-[#333333]">Quick Self-Test</span>
          </div>

          <p className="text-xs sm:text-sm font-semibold text-[#000000]">
            {lesson.comprehension_check.question}
          </p>

          <div className="space-y-1.5">
            {lesson.comprehension_check.options.map((option, idx) => {
              let style = 'bg-[#fefae0]/40 border-[#ccd5ae] text-[#000000] hover:bg-[#e9edc9]'
              if (hasAnswered) {
                if (idx === lesson.comprehension_check.correct_index) {
                  style = 'bg-[#ccd5ae] border-[#ccd5ae] text-[#000000] font-bold'
                } else if (idx === selectedAnswer) {
                  style = 'bg-red-100 border-red-300 text-[#000000] font-bold'
                } else {
                  style = 'opacity-50 border-[#ccd5ae] text-[#333333]'
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
                  className={`w-full text-left p-3 rounded-md border text-xs transition-all flex items-center justify-between cursor-pointer ${style}`}
                >
                  <span>{option}</span>
                  {hasAnswered && idx === lesson.comprehension_check.correct_index && (
                    <CheckCircle className="w-4 h-4 text-[#000000] shrink-0" />
                  )}
                </button>
              )
            })}
          </div>

          {hasAnswered && (
            <div className="p-3 bg-[#faedcd]/40 border border-[#ccd5ae] rounded text-xs space-y-0.5">
              <span className="font-bold text-[#000000]">Explanation:</span>
              <p className="text-[#333333] leading-relaxed">{lesson.comprehension_check.explanation}</p>
            </div>
          )}
        </div>

        {/* Previous and Next Navigation */}
        <div className="flex items-center justify-between pt-4 border-t border-[#ccd5ae]">
          {prevConcept ? (
            <button
              onClick={() => selectConcept(prevConcept.id)}
              className="btn-secondary text-xs"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Previous: {loc(prevConcept)}
            </button>
          ) : (
            <div />
          )}

          {nextConcept ? (
            <button
              onClick={() => selectConcept(nextConcept.id)}
              className="btn-primary text-xs"
            >
              Next: {loc(nextConcept)}
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          ) : (
            <button
              onClick={() => navigate('/student/practice')}
              className="btn-primary text-xs"
            >
              Go to Practice Arena
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
