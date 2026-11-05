import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  CheckSquare,
  Square,
  Plus,
  Trash2,
  ExternalLink,
  BookOpen,
  Target,
  FileCheck,
  CheckCircle2,
  Calendar,
  ListFilter,
  Loader2,
} from 'lucide-react'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { useI18n } from '@/i18n/I18nProvider'

interface TaskItem {
  id: string
  student_id: string
  title: string
  description?: string
  task_type: 'manual' | 'lesson' | 'practice' | 'test' | 'revision'
  link_type?: string
  link_id?: string
  link_payload?: any
  is_completed: boolean
  completed_at?: string
  due_date?: string
  created_at: string
}

export default function StudentTodoList() {
  const { t } = useI18n()
  const navigate = useNavigate()
  const { user } = useAuthStore()

  const [tasks, setTasks] = useState<TaskItem[]>([])
  const [filter, setFilter] = useState<'all' | 'pending' | 'completed'>('all')
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // New task form state
  const [newTitle, setNewTitle] = useState('')
  const [newTaskType, setNewTaskType] = useState<'manual' | 'lesson' | 'practice' | 'test' | 'revision'>('manual')
  const [showAddForm, setShowAddForm] = useState(false)

  const studentId = user?.id || ''

  const fetchTasks = async () => {
    if (!studentId) return
    try {
      setIsLoading(true)
      const res = await api.get(`/students/${studentId}/tasks`)
      setTasks(res.data)
    } catch (err) {
      console.error('Failed to load tasks:', err)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchTasks()
  }, [studentId])

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newTitle.trim()) return

    try {
      setIsSubmitting(true)
      const res = await api.post(`/students/${studentId}/tasks`, {
        title: newTitle.trim(),
        task_type: newTaskType,
      })
      setTasks((prev) => [res.data, ...prev])
      setNewTitle('')
      setShowAddForm(false)
    } catch (err) {
      console.error('Failed to create task:', err)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleToggleTask = async (task: TaskItem) => {
    try {
      const nextCompleted = !task.is_completed
      // Optimistic update
      setTasks((prev) =>
        prev.map((t) => (t.id === task.id ? { ...t, is_completed: nextCompleted } : t))
      )
      await api.patch(`/students/${studentId}/tasks/${task.id}`, {
        is_completed: nextCompleted,
      })
    } catch (err) {
      console.error('Failed to toggle task:', err)
      // Rollback on error
      fetchTasks()
    }
  }

  const handleDeleteTask = async (taskId: string) => {
    try {
      setTasks((prev) => prev.filter((t) => t.id !== taskId))
      await api.delete(`/students/${studentId}/tasks/${taskId}`)
    } catch (err) {
      console.error('Failed to delete task:', err)
      fetchTasks()
    }
  }

  const handleAddQuickTask = async (title: string, taskType: 'lesson' | 'practice' | 'test') => {
    try {
      const res = await api.post(`/students/${studentId}/tasks`, {
        title,
        task_type: taskType,
      })
      setTasks((prev) => [res.data, ...prev])
    } catch (err) {
      console.error('Failed to add quick task:', err)
    }
  }

  const filteredTasks = tasks.filter((t) => {
    if (filter === 'pending') return !t.is_completed
    if (filter === 'completed') return t.is_completed
    return true
  })

  const pendingCount = tasks.filter((t) => !t.is_completed).length
  const completedCount = tasks.filter((t) => t.is_completed).length

  const getTaskIcon = (type: string) => {
    switch (type) {
      case 'lesson':
        return <BookOpen className="w-4 h-4 text-[#000000]" />
      case 'practice':
        return <Target className="w-4 h-4 text-[#000000]" />
      case 'test':
        return <FileCheck className="w-4 h-4 text-[#000000]" />
      default:
        return <CheckSquare className="w-4 h-4 text-[#000000]" />
    }
  }

  const handleNavigateToTaskLink = (task: TaskItem) => {
    if (task.link_type === 'concept' && task.link_id) {
      navigate(`/student/learn?concept=${task.link_id}`)
    } else if (task.task_type === 'practice') {
      navigate('/student/practice')
    } else if (task.task_type === 'test') {
      navigate('/student/test')
    } else if (task.task_type === 'lesson') {
      navigate('/student/learn')
    }
  }

  return (
    <div className="max-w-4xl mx-auto py-6 px-4 space-y-6 text-[#000000]">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#ccd5ae] pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#000000] flex items-center gap-2">
            <CheckSquare className="w-6 h-6 text-[#d4a373]" />
            Academic To-Do List
          </h1>
          <p className="text-xs text-[#333333] mt-0.5">
            Plan, organize, and complete your NCERT learning activities.
          </p>
        </div>

        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="btn-primary self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          Add Learning Task
        </button>
      </div>

      {/* Quick Add Presets */}
      <div className="bg-[#faedcd]/40 border border-[#ccd5ae] rounded-lg p-3">
        <div className="text-xs font-semibold text-[#000000] mb-2 flex items-center gap-1.5">
          <span>Quick Actions</span>
        </div>
        <div className="flex flex-wrap gap-2 text-xs">
          <button
            onClick={() => handleAddQuickTask('Study next NCERT chapter lesson', 'lesson')}
            className="px-2.5 py-1.5 rounded-md bg-white border border-[#ccd5ae] hover:bg-[#e9edc9] text-[#000000] flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <BookOpen className="w-3.5 h-3.5" />
            + Study Lesson
          </button>
          <button
            onClick={() => handleAddQuickTask('Practise 10 questions on active topic', 'practice')}
            className="px-2.5 py-1.5 rounded-md bg-white border border-[#ccd5ae] hover:bg-[#e9edc9] text-[#000000] flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <Target className="w-3.5 h-3.5" />
            + Practice Questions
          </button>
          <button
            onClick={() => handleAddQuickTask('Complete weekly adaptive test', 'test')}
            className="px-2.5 py-1.5 rounded-md bg-white border border-[#ccd5ae] hover:bg-[#e9edc9] text-[#000000] flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <FileCheck className="w-3.5 h-3.5" />
            + Weekly Test
          </button>
        </div>
      </div>

      {/* Add Task Modal / Collapse Form */}
      {showAddForm && (
        <form
          onSubmit={handleCreateTask}
          className="bg-white border border-[#ccd5ae] rounded-lg p-4 shadow-xs space-y-3 animate-in fade-in"
        >
          <div className="flex items-center justify-between border-b border-[#ccd5ae] pb-2">
            <h3 className="text-sm font-bold text-[#000000]">New Learning Task</h3>
            <button
              type="button"
              onClick={() => setShowAddForm(false)}
              className="text-xs text-[#333333] hover:text-[#000000]"
            >
              Cancel
            </button>
          </div>

          <div>
            <label className="label">Task Title</label>
            <input
              type="text"
              required
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="e.g. Study Equations of Motion, Practise 10 Questions, Revise Chapter 3"
              className="input-field"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="label">Activity Category</label>
              <select
                value={newTaskType}
                onChange={(e) => setNewTaskType(e.target.value as any)}
                className="input-field"
              >
                <option value="manual">General Academic Task</option>
                <option value="lesson">NCERT Lesson Reading</option>
                <option value="practice">Topic Practice Session</option>
                <option value="test">Weekly Adaptive Test</option>
                <option value="revision">Chapter Revision</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setShowAddForm(false)}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !newTitle.trim()}
              className="btn-primary"
            >
              {isSubmitting ? 'Saving…' : 'Save Task'}
            </button>
          </div>
        </form>
      )}

      {/* Filter Tabs and Count Summary */}
      <div className="flex items-center justify-between border-b border-[#ccd5ae] pb-2 text-xs">
        <div className="flex items-center gap-1">
          <button
            onClick={() => setFilter('all')}
            className={`px-3 py-1 rounded-md font-semibold transition-all cursor-pointer ${
              filter === 'all'
                ? 'bg-[#ccd5ae] text-[#000000] border border-[#ccd5ae]'
                : 'text-[#333333] hover:bg-[#e9edc9]'
            }`}
          >
            All ({tasks.length})
          </button>
          <button
            onClick={() => setFilter('pending')}
            className={`px-3 py-1 rounded-md font-semibold transition-all cursor-pointer ${
              filter === 'pending'
                ? 'bg-[#ccd5ae] text-[#000000] border border-[#ccd5ae]'
                : 'text-[#333333] hover:bg-[#e9edc9]'
            }`}
          >
            Pending ({pendingCount})
          </button>
          <button
            onClick={() => setFilter('completed')}
            className={`px-3 py-1 rounded-md font-semibold transition-all cursor-pointer ${
              filter === 'completed'
                ? 'bg-[#ccd5ae] text-[#000000] border border-[#ccd5ae]'
                : 'text-[#333333] hover:bg-[#e9edc9]'
            }`}
          >
            Completed ({completedCount})
          </button>
        </div>

        <span className="text-[11px] text-[#333333]">
          {completedCount} of {tasks.length} tasks completed
        </span>
      </div>

      {/* Task List */}
      <div className="space-y-2">
        {isLoading ? (
          <div className="py-12 text-center text-[#333333]">
            <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2 text-[#000000]" />
            <p className="text-xs">Loading tasks…</p>
          </div>
        ) : filteredTasks.length === 0 ? (
          <div className="py-12 text-center bg-white border border-[#ccd5ae] rounded-lg p-6">
            <CheckCircle2 className="w-8 h-8 mx-auto mb-2 text-[#ccd5ae]" />
            <p className="text-sm font-bold text-[#000000]">
              {filter === 'completed' ? 'No completed tasks yet' : 'No tasks in this view'}
            </p>
            <p className="text-xs text-[#333333] mt-1">
              Add your learning tasks above or click a quick action to start organizing your study plan.
            </p>
          </div>
        ) : (
          filteredTasks.map((task) => (
            <div
              key={task.id}
              className={`flex items-center justify-between p-3.5 rounded-lg border transition-all ${
                task.is_completed
                  ? 'bg-[#faedcd]/20 border-[#ccd5ae] opacity-75'
                  : 'bg-white border-[#ccd5ae] shadow-2xs hover:border-[#d4a373]'
              }`}
            >
              <div className="flex items-center gap-3 min-w-0">
                <button
                  type="button"
                  onClick={() => handleToggleTask(task)}
                  className="text-[#000000] hover:text-[#d4a373] transition-colors shrink-0 cursor-pointer"
                >
                  {task.is_completed ? (
                    <CheckSquare className="w-5 h-5 text-[#d4a373]" />
                  ) : (
                    <Square className="w-5 h-5 text-[#333333]" />
                  )}
                </button>

                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs font-semibold text-[#000000] truncate ${
                        task.is_completed ? 'line-through text-[#666666]' : ''
                      }`}
                    >
                      {task.title}
                    </span>
                    <span className="text-[10px] font-medium uppercase px-1.5 py-0.2 rounded bg-[#e9edc9] text-[#000000] border border-[#ccd5ae] shrink-0">
                      {task.task_type}
                    </span>
                  </div>
                  {task.description && (
                    <p className="text-[11px] text-[#333333] truncate mt-0.5">
                      {task.description}
                    </p>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0 ml-3">
                {(task.link_type || task.task_type !== 'manual') && (
                  <button
                    onClick={() => handleNavigateToTaskLink(task)}
                    className="p-1.5 rounded bg-[#faedcd] hover:bg-[#e9edc9] border border-[#ccd5ae] text-[#000000] text-xs flex items-center gap-1 transition-colors cursor-pointer"
                    title="Open Learning Activity"
                  >
                    {getTaskIcon(task.task_type)}
                    <span className="hidden sm:inline text-[11px]">Go</span>
                    <ExternalLink className="w-3 h-3" />
                  </button>
                )}

                <button
                  onClick={() => handleDeleteTask(task.id)}
                  className="p-1.5 rounded hover:bg-red-50 text-[#666666] hover:text-red-700 transition-colors cursor-pointer"
                  title="Delete Task"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
