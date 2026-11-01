import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { GitFork, BookOpen, Layers, ArrowRight, CheckCircle2, ChevronRight, Info } from 'lucide-react'
import { useI18n } from '@/i18n/I18nProvider'
import PageHeader from '@/components/PageHeader'
import LoadingSpinner from '@/components/LoadingSpinner'
import ErrorMessage from '@/components/ErrorMessage'
import api from '@/lib/api'

interface ConceptNode {
  id: string
  code: string
  name: string
  name_te?: string
  name_hi?: string
  grade: number
  difficulty: string
  objectives: string[]
}

interface PrereqEdge {
  id: string
  source: string // prerequisite concept id
  target: string // dependent concept id
  is_strict: boolean
  weight: number
}

interface GraphData {
  nodes: ConceptNode[]
  edges: PrereqEdge[]
}

export default function AdminCurriculum() {
  const { t } = useI18n()
  const [activeTab, setActiveTab] = useState<'subjects' | 'graph'>('graph')
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [subjectFilter, setSubjectFilter] = useState<string>('all')

  const { data: subjectData, isLoading: isSubLoading, isError: isSubError, refetch: refetchSub } = useQuery({
    queryKey: ['curriculum-subjects'],
    queryFn: async () => {
      const res = await api.get('/curriculum/subjects?board_code=CBSE')
      return res.data
    },
  })

  const { data: graphData, isLoading: isGraphLoading, isError: isGraphError, refetch: refetchGraph } = useQuery<GraphData>({
    queryKey: ['curriculum-graph'],
    queryFn: async () => {
      const res = await api.get('/curriculum/graph')
      return res.data
    },
  })

  if (isSubLoading || isGraphLoading) return <LoadingSpinner />
  if (isSubError || isGraphError) return <ErrorMessage onRetry={() => { refetchSub(); refetchGraph() }} />

  const subjects: any[] = subjectData?.subjects ?? []
  const nodes = graphData?.nodes ?? []
  const edges = graphData?.edges ?? []

  // Filtered nodes
  const filteredNodes = nodes.filter((n) => {
    if (subjectFilter === 'all') return true
    if (subjectFilter === 'sci') return n.code.startsWith('sci')
    if (subjectFilter === 'math') return n.code.startsWith('math')
    if (subjectFilter === 'eng') return n.code.startsWith('eng')
    if (subjectFilter === 'sst') return n.code.startsWith('sst')
    return true
  })

  // Selected node details
  const selectedNode = nodes.find((n) => n.id === selectedNodeId)
  const incomingEdges = edges.filter((e) => e.target === selectedNodeId)
  const outgoingEdges = edges.filter((e) => e.source === selectedNodeId)

  // Group nodes by grade
  const grades = [6, 7, 8, 9, 10]
  const nodesByGrade: Record<number, ConceptNode[]> = { 6: [], 7: [], 8: [], 9: [], 10: [] }
  filteredNodes.forEach((n) => {
    if (nodesByGrade[n.grade]) nodesByGrade[n.grade].push(n)
  })

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <PageHeader
          title={t('nav_curriculum')}
          subtitle="CBSE Class 6–10 concept taxonomy & prerequisite dependency graph"
        />

        {/* View Toggle Tabs */}
        <div className="flex p-1 bg-slate-100 rounded-lg border border-slate-200 self-start sm:self-auto">
          <button
            onClick={() => setActiveTab('graph')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition ${
              activeTab === 'graph' ? 'bg-white shadow text-primary-900' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <GitFork className="w-3.5 h-3.5 text-primary-700" />
            <span>Prerequisite Graph (DAG)</span>
          </button>
          <button
            onClick={() => setActiveTab('subjects')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition ${
              activeTab === 'subjects' ? 'bg-white shadow text-primary-900' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Layers className="w-3.5 h-3.5 text-slate-700" />
            <span>Subjects Directory</span>
          </button>
        </div>
      </div>

      {activeTab === 'graph' ? (
        <div className="space-y-6">
          {/* Controls & Filter Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 p-4 bg-white rounded-xl border border-slate-200 shadow-sm">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-700">Filter Domain:</span>
              {(['all', 'sci', 'math', 'eng', 'sst'] as const).map((s) => (
                <button
                  key={s}
                  onClick={() => setSubjectFilter(s)}
                  className={`text-xs px-2.5 py-1 rounded-full font-medium transition ${
                    subjectFilter === s
                      ? 'bg-primary-900 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {s === 'all' ? 'All Subjects' : s.toUpperCase()}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-4 text-xs text-slate-500">
              <span className="flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                {filteredNodes.length} Concepts
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-full bg-primary-600" />
                {edges.length} Dependency Edges
              </span>
            </div>
          </div>

          {/* Visual DAG Columns Layout */}
          <div className="card p-6 bg-slate-50/50 border border-slate-200 rounded-2xl overflow-x-auto">
            <div className="min-w-[800px] grid grid-cols-5 gap-4">
              {grades.map((grade) => (
                <div key={grade} className="flex flex-col space-y-3">
                  <div className="p-2 rounded-lg bg-slate-200/70 border border-slate-300 text-center">
                    <span className="text-xs font-bold text-slate-800">Class {grade}</span>
                    <span className="text-[10px] text-slate-500 block">
                      {nodesByGrade[grade]?.length || 0} concept(s)
                    </span>
                  </div>

                  <div className="space-y-3 flex-1">
                    {nodesByGrade[grade]?.length === 0 ? (
                      <div className="h-24 border border-dashed border-slate-200 rounded-xl flex items-center justify-center text-[11px] text-slate-400">
                        None in scope
                      </div>
                    ) : (
                      nodesByGrade[grade].map((node) => {
                        const isSelected = selectedNodeId === node.id
                        const hasPrereq = edges.some((e) => e.target === node.id)
                        const isPrereqFor = edges.some((e) => e.source === node.id)

                        return (
                          <div
                            key={node.id}
                            onClick={() => setSelectedNodeId(node.id)}
                            className={`p-3 rounded-xl border text-left cursor-pointer transition-all shadow-sm ${
                              isSelected
                                ? 'bg-primary-900 text-white border-primary-950 ring-2 ring-primary-500 shadow-md'
                                : 'bg-white hover:border-primary-400 text-slate-800 border-slate-200'
                            }`}
                          >
                            <div className="flex items-center justify-between gap-1 mb-1.5">
                              <span
                                className={`text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded ${
                                  isSelected ? 'bg-primary-800 text-primary-100' : 'bg-slate-100 text-slate-600'
                                }`}
                              >
                                {node.code}
                              </span>
                              <span
                                className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full capitalize ${
                                  isSelected
                                    ? 'bg-primary-800 text-primary-200'
                                    : node.difficulty === 'easy'
                                    ? 'bg-emerald-50 text-emerald-700'
                                    : node.difficulty === 'hard'
                                    ? 'bg-purple-50 text-purple-700'
                                    : 'bg-amber-50 text-amber-700'
                                }`}
                              >
                                {node.difficulty}
                              </span>
                            </div>

                            <div className={`text-xs font-bold leading-snug ${isSelected ? 'text-white' : 'text-slate-900'}`}>
                              {node.name}
                            </div>

                            {/* Prerequisite indicators */}
                            <div className="mt-2.5 pt-2 border-t border-slate-100/50 flex items-center justify-between text-[10px]">
                              {hasPrereq ? (
                                <span className={isSelected ? 'text-primary-200' : 'text-amber-600'}>
                                  ← Has Prerequisite
                                </span>
                              ) : (
                                <span className={isSelected ? 'text-primary-300' : 'text-slate-400'}>
                                  ● Root Concept
                                </span>
                              )}
                              {isPrereqFor && (
                                <span className={isSelected ? 'text-primary-200' : 'text-primary-600'}>
                                  Unlocks Next →
                                </span>
                              )}
                            </div>
                          </div>
                        )
                      })
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Node Inspector Drawer */}
          {selectedNode ? (
            <div className="p-5 bg-white rounded-2xl border border-primary-200 shadow-md space-y-4 animate-in fade-in">
              <div className="flex items-start justify-between border-b pb-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs px-2 py-0.5 rounded bg-primary-100 text-primary-800 font-bold">
                      {selectedNode.code}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-semibold">
                      Class {selectedNode.grade}
                    </span>
                  </div>
                  <h3 className="text-lg font-bold text-slate-900 mt-1">{selectedNode.name}</h3>
                </div>
                <button
                  onClick={() => setSelectedNodeId(null)}
                  className="text-slate-400 hover:text-slate-600 text-xs font-medium"
                >
                  ✕ Close
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Incoming Prerequisites */}
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <h4 className="text-xs font-bold uppercase text-slate-700 mb-2 flex items-center gap-1.5">
                    <ArrowRight className="w-3.5 h-3.5 text-amber-600 rotate-180" />
                    Direct Prerequisites (Ancestors in DAG)
                  </h4>
                  {incomingEdges.length === 0 ? (
                    <p className="text-xs text-slate-500 italic">This is a foundational root concept (no prior prerequisites required).</p>
                  ) : (
                    <div className="space-y-2">
                      {incomingEdges.map((e) => {
                        const parentNode = nodes.find((n) => n.id === e.source)
                        return (
                          <div key={e.id} className="p-2 bg-white rounded-lg border border-slate-200 text-xs flex items-center justify-between">
                            <div>
                              <span className="font-semibold text-slate-900">{parentNode?.name}</span>
                              <span className="text-slate-500 block text-[10px]">
                                Class {parentNode?.grade} · Weight: {e.weight} ({e.is_strict ? 'Strict' : 'Soft'})
                              </span>
                            </div>
                            <span className="text-amber-600 font-semibold text-[10px]">Prerequisite</span>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>

                {/* Outgoing Successors */}
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <h4 className="text-xs font-bold uppercase text-slate-700 mb-2 flex items-center gap-1.5">
                    <ArrowRight className="w-3.5 h-3.5 text-primary-600" />
                    Dependent Concepts (Successors in DAG)
                  </h4>
                  {outgoingEdges.length === 0 ? (
                    <p className="text-xs text-slate-500 italic">Terminal level in current curriculum scope.</p>
                  ) : (
                    <div className="space-y-2">
                      {outgoingEdges.map((e) => {
                        const childNode = nodes.find((n) => n.id === e.target)
                        return (
                          <div key={e.id} className="p-2 bg-white rounded-lg border border-slate-200 text-xs flex items-center justify-between">
                            <div>
                              <span className="font-semibold text-slate-900">{childNode?.name}</span>
                              <span className="text-slate-500 block text-[10px]">
                                Class {childNode?.grade} · Weight: {e.weight}
                              </span>
                            </div>
                            <span className="text-primary-600 font-semibold text-[10px]">Unlocks</span>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              </div>

              {/* Learning Objectives */}
              {selectedNode.objectives && selectedNode.objectives.length > 0 && (
                <div className="pt-2">
                  <h4 className="text-xs font-bold text-slate-700 mb-1.5">Official NCERT Learning Objectives:</h4>
                  <ul className="space-y-1">
                    {selectedNode.objectives.map((obj, i) => (
                      <li key={i} className="text-xs text-slate-600 flex items-start gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                        <span>{obj}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div className="p-4 bg-primary-50/60 border border-primary-200 rounded-xl flex items-center gap-3 text-xs text-primary-900">
              <Info className="w-4 h-4 text-primary-700 shrink-0" />
              <span>Click on any concept card in the graph above to inspect its prerequisite chain and dependency connections.</span>
            </div>
          )}
        </div>
      ) : (
        /* Subjects Directory View */
        <div className="grid gap-4">
          {subjects.map((s: any) => (
            <div key={s.id} className="card p-5 bg-white border border-slate-200 rounded-xl shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-slate-900 text-base">{s.name_en}</h3>
                  <p className="text-xs text-slate-500 mt-0.5 uppercase tracking-wide">{s.domain}</p>
                </div>
                <span className="badge badge-blue font-mono font-bold">{s.code}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
