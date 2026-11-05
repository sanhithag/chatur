import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Heart, TrendingUp, BookOpen, UserPlus, Flame, Star, CheckCircle2, AlertCircle } from 'lucide-react'
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
          className="h-full rounded-full transition-all duration-300 bg-[#d4a373]"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-bold text-[#000000] w-9 text-right">{pct}%</span>
    </div>
  )
}

export default function ParentDashboard() {
  const { t } = useI18n()
  const user = useAuthStore((s) => s.user)
  const queryClient = useQueryClient()

  const [selectedChildId, setSelectedChildId] = useState<string | null>(null)
  const [showLinkModal, setShowLinkModal] = useState(false)
  const [childUsername, setChildUsername] = useState('')
  const [relationship, setRelationship] = useState('Parent')
  const [linkError, setLinkError] = useState<string | null>(null)

  // Fetch linked children
  const childrenQuery = useQuery({
    queryKey: ['parent-children', user?.id],
    queryFn: async () => {
      const res = await api.get(`/parents/${user?.id}/children`)
      return res.data
    },
    enabled: !!user?.id,
  })

  const childrenData = childrenQuery.data
  const children: any[] = Array.isArray(childrenData)
    ? childrenData
    : (childrenData?.children ?? [])

  const activeChild = selectedChildId
    ? children.find((c: any) => c.student_id === selectedChildId) || children[0]
    : children[0]

  // Fetch progress for active child
  const progressQuery = useQuery({
    queryKey: ['child-progress', user?.id, activeChild?.student_id],
    queryFn: async () => {
      const res = await api.get(`/parents/${user?.id}/children/${activeChild.student_id}/progress`)
      return res.data
    },
    enabled: !!user?.id && !!activeChild?.student_id,
  })

  // Link child mutation
  const linkMutation = useMutation({
    mutationFn: async () => {
      setLinkError(null)
      const res = await api.post(`/parents/${user?.id}/link-child`, {
        student_username: childUsername,
        relationship: relationship,
      })
      return res.data
    },
    onSuccess: () => {
      setShowLinkModal(false)
      setChildUsername('')
      queryClient.invalidateQueries({ queryKey: ['parent-children', user?.id] })
    },
    onError: (err: any) => {
      setLinkError(err?.response?.data?.detail || 'Failed to link child. Check username and try again.')
    },
  })

  if (childrenQuery.isLoading) return <LoadingSpinner />
  if (childrenQuery.isError) return <ErrorMessage onRetry={childrenQuery.refetch} />

  const progress = progressQuery.data
  const conceptProgress: any[] = progress?.concept_progress ?? progress?.concepts ?? []

  return (
    <div className="p-4 lg:p-8 max-w-4xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#ccd5ae] pb-4">
        <div>
          <h1 className="text-2xl font-black text-[#000000] flex items-center gap-2">
            <Heart className="w-6 h-6 text-[#000000]" />
            Child Academic Progress
          </h1>
          <p className="text-xs sm:text-sm text-[#333333] mt-1">
            Monitor your child's syllabus progress, practice activities, and test performance.
          </p>
        </div>
        <button
          onClick={() => setShowLinkModal(true)}
          className="btn-primary self-start sm:self-auto text-xs px-3.5 py-2 font-bold flex items-center gap-1.5 cursor-pointer"
        >
          <UserPlus className="w-4 h-4 text-[#000000]" />
          <span>Link Child Account</span>
        </button>
      </div>

      {children.length === 0 ? (
        <div className="bg-white rounded-xl border border-[#ccd5ae] p-10 text-center shadow-sm">
          <Heart className="w-12 h-12 text-[#ccd5ae] mx-auto mb-3" />
          <h3 className="text-base font-bold text-[#000000]">No Children Linked Yet</h3>
          <p className="text-xs text-[#333333] max-w-sm mx-auto mt-1 mb-5">
            Link your child's student account to view their real-time syllabus mastery, test scores, and study habits.
          </p>
          <button
            onClick={() => setShowLinkModal(true)}
            className="btn-primary px-4 py-2 text-xs font-bold"
          >
            Link a Child Account Now
          </button>
        </div>
      ) : (
        <>
          {/* Child selection tabs */}
          {children.length > 1 && (
            <div className="flex gap-2 border-b border-[#ccd5ae] pb-2">
              {children.map((c: any) => {
                const isSelected = activeChild?.student_id === c.student_id
                return (
                  <button
                    key={c.student_id}
                    onClick={() => setSelectedChildId(c.student_id)}
                    className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all border cursor-pointer ${
                      isSelected
                        ? 'bg-[#d4a373] text-[#000000] border-[#ccd5ae]'
                        : 'bg-[#faedcd] text-[#333333] border-[#ccd5ae] hover:text-[#000000]'
                    }`}
                  >
                    {c.student_name || c.name} (Class {c.grade})
                  </button>
                )
              })}
            </div>
          )}

          {/* Child Card Header */}
          {activeChild && (
            <div className="bg-white rounded-xl border border-[#ccd5ae] p-5 shadow-sm space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#ccd5ae]">
                <div className="flex items-center gap-3.5">
                  <div className="w-12 h-12 rounded-xl bg-[#faedcd] border border-[#ccd5ae] text-[#000000] flex items-center justify-center font-black text-lg">
                    {(activeChild.student_name || activeChild.name || 'S').charAt(0)}
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-[#000000]">{activeChild.student_name || activeChild.name}</h2>
                    <p className="text-xs text-[#333333]">
                      Class {activeChild.grade} • Section {activeChild.section || 'A'} • CBSE Board
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="px-3 py-1.5 rounded-xl bg-[#faedcd] border border-[#ccd5ae] text-center">
                    <div className="text-[10px] uppercase font-bold text-[#333333]">XP Points</div>
                    <div className="text-base font-black text-[#000000] flex items-center justify-center gap-1">
                      <Star className="w-3.5 h-3.5 text-[#000000]" />
                      {activeChild.total_xp ?? 0}
                    </div>
                  </div>
                  <div className="px-3 py-1.5 rounded-xl bg-[#faedcd] border border-[#ccd5ae] text-center">
                    <div className="text-[10px] uppercase font-bold text-[#333333]">Daily Streak</div>
                    <div className="text-base font-black text-[#000000] flex items-center justify-center gap-1">
                      <Flame className="w-3.5 h-3.5 text-[#000000]" />
                      {activeChild.current_streak ?? 0}d
                    </div>
                  </div>
                </div>
              </div>

              {/* Weekly Pedagogical Tip */}
              <div className="p-3.5 rounded-lg bg-[#faedcd]/60 border border-[#ccd5ae] text-xs text-[#000000] leading-relaxed">
                <span className="font-bold uppercase tracking-wider block mb-1 text-[11px] text-[#000000]">
                  Academic Recommendation
                </span>
                <p className="text-[#333333]">
                  Consistent 20-minute daily practice sessions in core concepts strengthen long-term memory retention. Encourage reviewing the Learn section before attempting weekly tests.
                </p>
              </div>
            </div>
          )}

          {/* Child Subject Progress */}
          {progressQuery.isLoading ? (
            <LoadingSpinner />
          ) : (
            <div className="bg-white rounded-xl border border-[#ccd5ae] shadow-sm overflow-hidden">
              <div className="p-4 border-b border-[#ccd5ae] flex items-center justify-between bg-[#faedcd]/40">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-[#000000]" />
                  <h3 className="font-bold text-[#000000] text-sm uppercase tracking-wider">
                    Topic Mastery
                  </h3>
                </div>
                <span className="text-xs font-bold text-[#333333]">
                  {conceptProgress.length} topics tracked
                </span>
              </div>

              <div className="p-4 space-y-3">
                {conceptProgress.length === 0 ? (
                  <p className="text-xs text-[#333333] py-6 text-center">No learning activity recorded yet.</p>
                ) : (
                  conceptProgress.map((cp: any) => {
                    const isOnTrack = cp.on_track ?? cp.p_know >= 0.5
                    return (
                      <div key={cp.concept_id} className="p-3 rounded-lg border border-[#ccd5ae] bg-white">
                        <div className="flex justify-between items-center mb-1.5">
                          <span className="text-sm font-bold text-[#000000]">
                            {cp.concept_name || cp.name}
                          </span>
                          <span className={`text-xs font-bold px-2 py-0.5 rounded border ${
                            isOnTrack
                              ? 'bg-[#e9edc9] text-[#000000] border-[#ccd5ae]'
                              : 'bg-[#faedcd] text-[#000000] border-[#ccd5ae]'
                          }`}>
                            {isOnTrack ? 'On Track' : 'Needs Practice'}
                          </span>
                        </div>
                        <MasteryBar value={cp.p_know} />
                      </div>
                    )
                  })
                )}
              </div>
            </div>
          )}
        </>
      )}

      {/* Link Child Modal */}
      {showLinkModal && (
        <div className="fixed inset-0 bg-[#000000]/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl border border-[#ccd5ae] animate-in fade-in">
            <h3 className="text-base font-bold text-[#000000] mb-1">Link Child Account</h3>
            <p className="text-xs text-[#333333] mb-4">
              Enter your child's student username to monitor their learning progress.
            </p>

            <form
              onSubmit={(e) => {
                e.preventDefault()
                linkMutation.mutate()
              }}
              className="space-y-4"
            >
              <div>
                <label className="block text-xs font-bold text-[#000000] uppercase mb-1">
                  Student Username
                </label>
                <input
                  type="text"
                  placeholder="e.g. student1"
                  value={childUsername}
                  onChange={(e) => setChildUsername(e.target.value)}
                  className="input-field w-full bg-white border border-[#ccd5ae] text-[#000000]"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-[#000000] uppercase mb-1">
                  Relationship
                </label>
                <select
                  value={relationship}
                  onChange={(e) => setRelationship(e.target.value)}
                  className="input-field w-full bg-white border border-[#ccd5ae] text-[#000000]"
                >
                  <option value="Parent">Parent</option>
                  <option value="Guardian">Guardian</option>
                  <option value="Mother">Mother</option>
                  <option value="Father">Father</option>
                </select>
              </div>

              {linkError && (
                <div className="p-3 text-xs text-rose-900 bg-rose-100 border border-rose-300 rounded-lg">
                  {linkError}
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2 border-t border-[#ccd5ae]">
                <button
                  type="button"
                  onClick={() => setShowLinkModal(false)}
                  className="btn-secondary text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={linkMutation.isPending || !childUsername.trim()}
                  className="btn-primary text-xs font-bold"
                >
                  {linkMutation.isPending ? 'Linking…' : 'Link Account'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
