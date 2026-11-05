import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useSearchParams, useNavigate } from 'react-router-dom'
import {
  Target,
  Flame,
  Star,
  Lightbulb,
  CheckCircle2,
  XCircle,
  ArrowRight,
  RotateCcw,
  Clock,
  History,
  BookOpen,
  Sparkles,
  HelpCircle,
  Filter,
  Check,
} from 'lucide-react'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { useI18n } from '@/i18n/I18nProvider'
import LoadingSpinner from '@/components/LoadingSpinner'
import ErrorMessage from '@/components/ErrorMessage'

interface PracticeFilters {
  grades: Array<{
    grade: number
    subjects: Array<{
      id: string
      code: string
      name: string
      domain: string
      chapters: Array<{
        id: string
        chapter_no: number
        name: string
        topics: Array<{
          id: string
          topic_no: number
          name: string
        }>
      }>
    }>
  }>
}

interface PracticeQuestion {
  id: string
  concept_id: string
  concept_name: string
  difficulty: number
  difficulty_label: string
  body: string
  options: string[]
  hints: string[]
}

interface PracticeSession {
  session_id: string
  title: string
  total_questions: number
  difficulty: string
  questions: PracticeQuestion[]
  streak: number
  xp: number
}

interface PracticeSessionResult {
  attempt_id: string
  score: number
  total: number
  accuracy_pct: number
  earned_xp: number
  new_total_xp: number
  current_streak: number
  results: Array<{
    question_id: string
    concept_id: string
    concept_name: string
    question_text: string
    options: string[]
    selected_option: number
    correct_option: number
    is_correct: boolean
    explanation: string
  }>
}

interface PracticeHistoryItem {
  attempt_id: string
  date: string
  title: string
  score: number
  max_score: number
  accuracy_pct: number
  time_spent_mins: number
}

export default function StudentPractice() {
  const { t, lang } = useI18n()
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const queryClient = useQueryClient()
  const [searchParams] = useSearchParams()

  const paramConceptId = searchParams.get('concept_id')

  // Top Tabs: 'practice' or 'history'
  const [activeTab, setActiveTab] = useState<'practice' | 'history'>('practice')

  // Configuration Filter State
  const [selectedGrade, setSelectedGrade] = useState<number>(9)
  const [selectedSubjectId, setSelectedSubjectId] = useState<string>('')
  const [selectedChapterId, setSelectedChapterId] = useState<string>('')
  const [selectedTopicId, setSelectedTopicId] = useState<string>('')
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('all')
  const [questionCount, setQuestionCount] = useState<number>(5)

  // Active Session State
  const [session, setSession] = useState<PracticeSession | null>(null)
  const [currentIdx, setCurrentIdx] = useState<number>(0)
  const [answers, setAnswers] = useState<Record<string, { option: number; hintsUsed: number; timeSpent: number }>>({})
  const [revealedHints, setRevealedHints] = useState<Record<string, number>>({})
  const [sessionResult, setSessionResult] = useState<PracticeSessionResult | null>(null)

  // Fetch cascading filter options
  const { data: filtersData, isLoading: isLoadingFilters } = useQuery<PracticeFilters>({
    queryKey: ['practice-filters', user?.id],
    queryFn: async () => (await api.get(`/students/${user?.id}/practice/filters`)).data,
    enabled: !!user?.id,
  })

  // Set defaults once filters load
  const availableGrades = filtersData?.grades || []
  const currentGradeItem = availableGrades.find((g) => g.grade === selectedGrade) || availableGrades[0]
  const availableSubjects = currentGradeItem?.subjects || []
  const currentSubjectItem = availableSubjects.find((s) => s.id === selectedSubjectId) || availableSubjects[0]
  const availableChapters = currentSubjectItem?.chapters || []
  const currentChapterItem = availableChapters.find((c) => c.id === selectedChapterId)
  const availableTopics = currentChapterItem?.topics || []

  // Fetch Practice History
  const { data: historyList, isLoading: isLoadingHistory, refetch: refetchHistory } = useQuery<PracticeHistoryItem[]>({
    queryKey: ['practice-history', user?.id],
    queryFn: async () => (await api.get(`/students/${user?.id}/practice/history`)).data,
    enabled: !!user?.id && activeTab === 'history',
  })

  // Start Practice Session Mutation
  const startSessionMutation = useMutation({
    mutationFn: async () => {
      const payload = {
        grade: selectedGrade,
        subject_id: selectedSubjectId || undefined,
        chapter_id: selectedChapterId || undefined,
        topic_id: selectedTopicId || undefined,
        concept_id: paramConceptId || undefined,
        difficulty: selectedDifficulty,
        count: questionCount,
        lang,
      }
      const res = await api.post(`/students/${user?.id}/practice/session`, payload)
      return res.data as PracticeSession
    },
    onSuccess: (data) => {
      setSession(data)
      setCurrentIdx(0)
      setAnswers({})
      setRevealedHints({})
      setSessionResult(null)
    },
  })

  // Submit Practice Session Mutation
  const submitSessionMutation = useMutation({
    mutationFn: async (): Promise<PracticeSessionResult> => {
      if (!session) throw new Error('No active session')
      const formattedResponses = session.questions.map((q) => {
        const ans = answers[q.id]
        return {
          question_id: q.id,
          selected_option: ans ? ans.option : 0,
          hints_used: revealedHints[q.id] || 0,
          time_spent_secs: 15,
        }
      })
      const res = await api.post(`/students/${user?.id}/practice/session/submit`, {
        session_id: session.session_id,
        responses: formattedResponses,
      })
      return res.data as PracticeSessionResult
    },
    onSuccess: (data: PracticeSessionResult) => {
      setSessionResult(data)
      queryClient.invalidateQueries({ queryKey: ['student-dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['practice-history'] })
    },
  })

  const currentQ = session?.questions[currentIdx]
  const isLastQuestion = session ? currentIdx === session.questions.length - 1 : false
  const currentAnswer = currentQ ? answers[currentQ.id]?.option : undefined

  const handleSelectOption = (optIdx: number) => {
    if (!currentQ) return
    setAnswers((prev) => ({
      ...prev,
      [currentQ.id]: {
        option: optIdx,
        hintsUsed: revealedHints[currentQ.id] || 0,
        timeSpent: 10,
      },
    }))
  }

  const handleRevealNextHint = () => {
    if (!currentQ) return
    const currentHintsCount = revealedHints[currentQ.id] || 0
    if (currentHintsCount < currentQ.hints.length) {
      setRevealedHints((prev) => ({
        ...prev,
        [currentQ.id]: currentHintsCount + 1,
      }))
    }
  }

  const resetSession = () => {
    setSession(null)
    setSessionResult(null)
    setCurrentIdx(0)
    setAnswers({})
    setRevealedHints({})
  }

  if (isLoadingFilters) return <LoadingSpinner />

  return (
    <div className="p-4 lg:p-8 max-w-5xl mx-auto space-y-6">
      {/* Module Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#ccd5ae] pb-4">
        <div>
          <h1 className="text-2xl font-black text-[#000000] flex items-center gap-2">
            <Target className="w-6 h-6 text-[#000000]" />
            Practice Questions
          </h1>
          <p className="text-xs sm:text-sm text-[#333333] mt-1">
            Solve NCERT topic-wise practice questions with step-by-step hints and full explanations.
          </p>
        </div>

        {!session && (
          <div className="flex items-center gap-1.5 p-1 bg-[#faedcd] border border-[#ccd5ae] rounded-xl self-start sm:self-auto">
            <button
              onClick={() => setActiveTab('practice')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                activeTab === 'practice'
                  ? 'bg-[#d4a373] text-[#000000] border border-[#ccd5ae]'
                  : 'text-[#333333] hover:text-[#000000]'
              }`}
            >
              New Practice
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
              Attempt History
            </button>
          </div>
        )}
      </div>

      {/* ─── TAB 1: PRACTICE SESSION / CONFIGURATOR ─────────────────────────── */}
      {activeTab === 'practice' && (
        <>
          {/* View A: Configurator (when not in session) */}
          {!session && (
            <div className="card p-6 bg-white border border-[#ccd5ae] space-y-6 shadow-sm">
              <div className="border-b border-[#ccd5ae] pb-3">
                <h2 className="text-base font-bold text-[#000000] flex items-center gap-2">
                  <Filter className="w-4 h-4 text-[#000000]" />
                  Configure Your Practice Session
                </h2>
                <p className="text-xs text-[#333333]">Select your class, subject and chapter to generate questions.</p>
              </div>

              {/* Class & Subject Pickers */}
              <div className="space-y-4">
                <div>
                  <label className="label text-xs font-bold text-[#000000]">1. Select Class</label>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {availableGrades.map((g) => (
                      <button
                        key={g.grade}
                        type="button"
                        onClick={() => {
                          setSelectedGrade(g.grade)
                          setSelectedSubjectId('')
                          setSelectedChapterId('')
                          setSelectedTopicId('')
                        }}
                        className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all cursor-pointer border ${
                          selectedGrade === g.grade
                            ? 'bg-[#ccd5ae] text-[#000000] border-[#ccd5ae]'
                            : 'bg-white border-[#ccd5ae] text-[#333333] hover:bg-[#e9edc9] hover:text-[#000000]'
                        }`}
                      >
                        Class {g.grade}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="label text-xs font-bold text-[#000000]">2. Select Subject</label>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 mt-1">
                    {availableSubjects.map((s) => {
                      const isSelected = selectedSubjectId === s.id
                      return (
                        <button
                          key={s.id}
                          type="button"
                          onClick={() => {
                            setSelectedSubjectId(s.id)
                            setSelectedChapterId('')
                            setSelectedTopicId('')
                          }}
                          className={`p-3 rounded-xl text-left border transition-all cursor-pointer ${
                            isSelected
                              ? 'bg-[#faedcd] border-2 border-[#d4a373] text-[#000000]'
                              : 'bg-white border-[#ccd5ae] text-[#000000] hover:bg-[#e9edc9]/50'
                          }`}
                        >
                          <div className="text-xs font-bold text-[#000000] truncate">{s.name}</div>
                          <div className="text-[10px] uppercase font-semibold text-[#333333] mt-0.5">
                            {s.domain}
                          </div>
                        </button>
                      )
                    })}
                  </div>
                </div>

                {/* Chapter & Topic Pickers */}
                {availableChapters.length > 0 && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                    <div>
                      <label className="label text-xs font-bold text-[#000000]">3. Chapter (Optional)</label>
                      <select
                        value={selectedChapterId}
                        onChange={(e) => {
                          setSelectedChapterId(e.target.value)
                          setSelectedTopicId('')
                        }}
                        className="input-field mt-1 cursor-pointer bg-white border border-[#ccd5ae] text-[#000000]"
                      >
                        <option value="">All Chapters</option>
                        {availableChapters.map((ch) => (
                          <option key={ch.id} value={ch.id}>
                            Ch {ch.chapter_no}: {ch.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="label text-xs font-bold text-[#000000]">4. Specific Topic (Optional)</label>
                      <select
                        value={selectedTopicId}
                        onChange={(e) => setSelectedTopicId(e.target.value)}
                        disabled={!selectedChapterId || availableTopics.length === 0}
                        className="input-field mt-1 cursor-pointer disabled:opacity-50 bg-white border border-[#ccd5ae] text-[#000000]"
                      >
                        <option value="">All Topics in Chapter</option>
                        {availableTopics.map((top) => (
                          <option key={top.id} value={top.id}>
                            Topic {top.topic_no}: {top.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                )}

                {/* Difficulty & Question Count */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                  <div>
                    <label className="label text-xs font-bold text-[#000000]">5. Difficulty Level</label>
                    <div className="grid grid-cols-4 gap-2 mt-1">
                      {[
                        { id: 'all', label: 'All' },
                        { id: 'easy', label: 'Easy' },
                        { id: 'medium', label: 'Medium' },
                        { id: 'hard', label: 'Hard' },
                      ].map((d) => (
                        <button
                          key={d.id}
                          type="button"
                          onClick={() => setSelectedDifficulty(d.id)}
                          className={`py-2 text-xs font-bold rounded-lg border text-center transition-all cursor-pointer ${
                            selectedDifficulty === d.id
                              ? 'bg-[#ccd5ae] text-[#000000] border-[#ccd5ae]'
                              : 'bg-white border-[#ccd5ae] text-[#333333] hover:text-[#000000] hover:bg-[#e9edc9]/40'
                          }`}
                        >
                          {d.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="label text-xs font-bold text-[#000000]">6. Number of Questions</label>
                    <div className="grid grid-cols-4 gap-2 mt-1">
                      {[3, 5, 10, 15].map((cnt) => (
                        <button
                          key={cnt}
                          type="button"
                          onClick={() => setQuestionCount(cnt)}
                          className={`py-2 text-xs font-bold rounded-lg border text-center transition-all cursor-pointer ${
                            questionCount === cnt
                              ? 'bg-[#ccd5ae] text-[#000000] border-[#ccd5ae]'
                              : 'bg-white border-[#ccd5ae] text-[#333333] hover:text-[#000000] hover:bg-[#e9edc9]/40'
                          }`}
                        >
                          {cnt} Qs
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Start Session Action */}
              <div className="pt-4 border-t border-[#ccd5ae] flex justify-end">
                <button
                  type="button"
                  onClick={() => startSessionMutation.mutate()}
                  disabled={startSessionMutation.isPending}
                  className="btn-primary text-sm px-6 py-2.5 font-bold cursor-pointer flex items-center gap-2"
                >
                  <Target className="w-4 h-4 text-[#000000]" />
                  <span>{startSessionMutation.isPending ? 'Preparing Questions…' : 'Start Practice Session'}</span>
                </button>
              </div>
            </div>
          )}

          {/* View B: Active Session in Progress */}
          {session && !sessionResult && currentQ && (
            <div className="space-y-6">
              {/* Session Top Status Bar */}
              <div className="card p-4 bg-[#faedcd] border border-[#ccd5ae] flex items-center justify-between">
                <div>
                  <div className="text-xs font-bold text-[#000000] uppercase tracking-wider">{session.title}</div>
                  <div className="text-sm font-extrabold text-[#000000] mt-0.5">
                    Question {currentIdx + 1} of {session.total_questions}
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-[#000000]">
                    <Flame className="w-4 h-4 text-[#d4a373]" />
                    <span>Streak: {session.streak}</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-xs font-bold text-[#000000]">
                    <Star className="w-4 h-4 text-[#d4a373]" />
                    <span>{session.xp} XP</span>
                  </div>
                  <button
                    onClick={resetSession}
                    className="text-xs text-[#333333] hover:text-red-700 font-bold cursor-pointer ml-2 underline"
                  >
                    Quit Session
                  </button>
                </div>
              </div>

              {/* Progress bar */}
              <div className="w-full bg-[#e9edc9] h-2 rounded-full overflow-hidden border border-[#ccd5ae]">
                <div
                  className="bg-[#d4a373] h-full transition-all duration-300"
                  style={{ width: `${((currentIdx + 1) / session.total_questions) * 100}%` }}
                />
              </div>

              {/* Main Question Card */}
              <div className="card p-6 bg-white border border-[#ccd5ae] space-y-6">
                <div className="flex items-center justify-between border-b border-[#ccd5ae] pb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold uppercase px-2.5 py-0.5 rounded-full bg-[#e9edc9] text-[#000000] border border-[#ccd5ae]">
                      {currentQ.concept_name}
                    </span>
                    <span className="text-[10px] font-bold uppercase px-2.5 py-0.5 rounded-full bg-[#faedcd] text-[#000000] border border-[#ccd5ae]">
                      {currentQ.difficulty_label}
                    </span>
                  </div>
                </div>

                <h3 className="text-base sm:text-lg font-bold text-[#000000] leading-relaxed">
                  {currentQ.body}
                </h3>

                {/* Options List */}
                <div className="space-y-2.5">
                  {currentQ.options.map((opt, oIdx) => {
                    const isSelected = currentAnswer === oIdx
                    return (
                      <button
                        key={oIdx}
                        onClick={() => handleSelectOption(oIdx)}
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
                            {String.fromCharCode(65 + oIdx)}
                          </span>
                          <span className="text-[#000000]">{opt}</span>
                        </div>
                        {isSelected && <Check className="w-4 h-4 text-[#000000] shrink-0" />}
                      </button>
                    )
                  })}
                </div>

                {/* Intelligent Hints Drawer */}
                {currentQ.hints && currentQ.hints.length > 0 && (
                  <div className="p-4 rounded-xl bg-[#faedcd]/60 border border-[#ccd5ae] space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-[#000000] flex items-center gap-1.5">
                        <Lightbulb className="w-4 h-4 text-[#000000]" />
                        Hints (Guided Learning)
                      </span>
                      {(revealedHints[currentQ.id] || 0) < currentQ.hints.length && (
                        <button
                          type="button"
                          onClick={handleRevealNextHint}
                          className="text-xs font-bold text-[#000000] underline hover:text-[#333333] cursor-pointer"
                        >
                          Reveal Hint {(revealedHints[currentQ.id] || 0) + 1}
                        </button>
                      )}
                    </div>

                    {(revealedHints[currentQ.id] || 0) > 0 ? (
                      <div className="space-y-2">
                        {currentQ.hints.slice(0, revealedHints[currentQ.id] || 0).map((hint, hIdx) => (
                          <div key={hIdx} className="p-2.5 rounded-lg bg-white border border-[#ccd5ae] text-xs text-[#000000]">
                            <span className="font-bold text-[#000000] mr-1.5">Hint {hIdx + 1}:</span>
                            <span className="text-[#333333]">{hint}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-[#333333]">
                        Need help? Click 'Reveal Hint' to view step-by-step guidance.
                      </p>
                    )}
                  </div>
                )}
              </div>

              {/* Question Navigation Palette & Action Buttons */}
              <div className="flex items-center justify-between">
                <button
                  disabled={currentIdx === 0}
                  onClick={() => setCurrentIdx((prev) => Math.max(0, prev - 1))}
                  className="btn-secondary text-xs disabled:opacity-40"
                >
                  Previous
                </button>

                <div className="flex items-center gap-2">
                  {session.questions.map((_, i) => (
                    <button
                      key={i}
                      onClick={() => setCurrentIdx(i)}
                      className={`w-7 h-7 rounded-lg text-xs font-bold transition-all border ${
                        currentIdx === i
                          ? 'bg-[#d4a373] text-[#000000] border-[#000000]'
                          : answers[session.questions[i].id] !== undefined
                          ? 'bg-[#ccd5ae] text-[#000000] border-[#ccd5ae]'
                          : 'bg-white border-[#ccd5ae] text-[#333333]'
                      }`}
                    >
                      {i + 1}
                    </button>
                  ))}
                </div>

                {isLastQuestion ? (
                  <button
                    onClick={() => submitSessionMutation.mutate()}
                    disabled={submitSessionMutation.isPending || Object.keys(answers).length === 0}
                    className="btn-primary text-xs px-5 py-2 font-bold cursor-pointer"
                  >
                    {submitSessionMutation.isPending ? 'Submitting…' : 'Finish & Submit'}
                  </button>
                ) : (
                  <button
                    onClick={() => setCurrentIdx((prev) => Math.min(session.questions.length - 1, prev + 1))}
                    className="btn-primary text-xs px-5 py-2 font-bold cursor-pointer flex items-center gap-1.5"
                  >
                    <span>Next</span>
                    <ArrowRight className="w-3.5 h-3.5 text-[#000000]" />
                  </button>
                )}
              </div>
            </div>
          )}

          {/* View C: Session Result & Answer Review */}
          {sessionResult && (
            <div className="card p-6 bg-white border border-[#ccd5ae] space-y-6 animate-in fade-in">
              <div className="text-center py-4 border-b border-[#ccd5ae] space-y-2">
                <div className="w-14 h-14 rounded-full bg-[#e9edc9] text-[#000000] font-bold flex items-center justify-center mx-auto border-2 border-[#ccd5ae]">
                  <CheckCircle2 className="w-7 h-7 text-[#000000]" />
                </div>
                <h2 className="text-2xl font-black text-[#000000]">Practice Session Complete</h2>
                <p className="text-xs text-[#333333]">Your answers have been evaluated and your learning progress has been saved.</p>

                <div className="flex items-center justify-center gap-6 pt-3">
                  <div className="text-center">
                    <div className="text-2xl font-black text-[#000000]">
                      {sessionResult.score} / {sessionResult.total}
                    </div>
                    <div className="text-[10px] font-bold uppercase tracking-wider text-[#333333]">Score</div>
                  </div>
                  <div className="w-px h-8 bg-[#ccd5ae]" />
                  <div className="text-center">
                    <div className="text-2xl font-black text-[#000000]">
                      {sessionResult.accuracy_pct}%
                    </div>
                    <div className="text-[10px] font-bold uppercase tracking-wider text-[#333333]">Accuracy</div>
                  </div>
                  <div className="w-px h-8 bg-[#ccd5ae]" />
                  <div className="text-center">
                    <div className="text-2xl font-black text-[#000000]">
                      +{sessionResult.earned_xp} XP
                    </div>
                    <div className="text-[10px] font-bold uppercase tracking-wider text-[#333333]">XP Gained</div>
                  </div>
                </div>
              </div>

              {/* Detailed Question Review List */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-[#000000]">Review & Explanations</h3>
                {sessionResult.results.map((res, i) => (
                  <div
                    key={res.question_id}
                    className={`p-4 rounded-xl border space-y-3 ${
                      res.is_correct ? 'bg-[#e9edc9]/40 border-[#ccd5ae]' : 'bg-rose-50/50 border-rose-300'
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-[#000000]">Q{i + 1}.</span>
                        <span className="font-semibold text-[#000000]">{res.concept_name}</span>
                      </div>
                      <span
                        className={`font-bold px-2 py-0.5 rounded text-[10px] uppercase border ${
                          res.is_correct ? 'bg-[#ccd5ae] text-[#000000] border-[#ccd5ae]' : 'bg-rose-100 text-rose-900 border-rose-300'
                        }`}
                      >
                        {res.is_correct ? 'Correct' : 'Incorrect'}
                      </span>
                    </div>

                    <p className="text-xs sm:text-sm font-medium text-[#000000]">{res.question_text}</p>

                    <div className="space-y-1.5 text-xs">
                      {res.options.map((opt, optIdx) => {
                        let optStyle = 'bg-white border-[#ccd5ae] text-[#333333]'
                        if (optIdx === res.correct_option) {
                          optStyle = 'bg-[#e9edc9] border-2 border-[#ccd5ae] text-[#000000] font-bold'
                        } else if (optIdx === res.selected_option && !res.is_correct) {
                          optStyle = 'bg-rose-100 border-2 border-rose-300 text-rose-900 font-bold'
                        }
                        return (
                          <div key={optIdx} className={`p-2.5 rounded-lg border flex items-center justify-between ${optStyle}`}>
                            <span className="text-[#000000]">{opt}</span>
                            {optIdx === res.correct_option && (
                              <span className="text-[10px] font-bold uppercase text-[#000000]">Correct Answer</span>
                            )}
                            {optIdx === res.selected_option && !res.is_correct && (
                              <span className="text-[10px] font-bold uppercase text-rose-900">Your Answer</span>
                            )}
                          </div>
                        )
                      })}
                    </div>

                    <div className="p-3 bg-white rounded-lg border border-[#ccd5ae] text-xs space-y-1">
                      <span className="font-bold text-[#000000]">Explanation:</span>
                      <p className="text-[#333333]">{res.explanation}</p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Actions */}
              <div className="flex items-center justify-between pt-4 border-t border-[#ccd5ae]">
                <button
                  onClick={resetSession}
                  className="btn-secondary text-xs flex items-center gap-1.5"
                >
                  <RotateCcw className="w-3.5 h-3.5 text-[#000000]" />
                  <span>Practise More</span>
                </button>

                <button
                  onClick={() => navigate('/student/dashboard')}
                  className="btn-primary text-xs"
                >
                  Return to Dashboard
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* ─── TAB 2: ATTEMPT HISTORY ────────────────────────────────────────── */}
      {activeTab === 'history' && (
        <div className="card p-6 bg-white border border-[#ccd5ae] space-y-4 shadow-sm">
          <div className="flex items-center justify-between border-b border-[#ccd5ae] pb-3">
            <div>
              <h2 className="text-base font-bold text-[#000000]">Practice Attempt History</h2>
              <p className="text-xs text-[#333333]">All completed practice submissions saved in your profile.</p>
            </div>
            <button
              onClick={() => refetchHistory()}
              className="text-xs font-bold text-[#000000] underline hover:text-[#333333] cursor-pointer"
            >
              Refresh History
            </button>
          </div>

          {isLoadingHistory ? (
            <LoadingSpinner />
          ) : !historyList || historyList.length === 0 ? (
            <div className="text-center py-12 text-[#333333]">
              <History className="w-8 h-8 mx-auto mb-2 text-[#333333]/40" />
              <p className="text-sm font-bold text-[#000000]">No practice history yet</p>
              <p className="text-xs text-[#333333] mt-1">Start a practice session above to track your progress.</p>
            </div>
          ) : (
            <div className="divide-y divide-[#ccd5ae]">
              {historyList.map((item) => (
                <div key={item.attempt_id} className="py-3.5 flex items-center justify-between">
                  <div className="space-y-0.5">
                    <div className="text-sm font-bold text-[#000000]">{item.title}</div>
                    <div className="text-xs text-[#333333]">
                      {new Date(item.date).toLocaleDateString()} • {item.time_spent_mins} min session
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="text-sm font-bold text-[#000000]">
                        {item.score} / {item.max_score}
                      </div>
                      <div className="text-[11px] font-bold text-[#333333]">
                        {item.accuracy_pct}% Accuracy
                      </div>
                    </div>
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
