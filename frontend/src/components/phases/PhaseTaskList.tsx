import { useState, useEffect, useCallback } from 'react'
import { Plus, Loader2 } from 'lucide-react'
import { TaskCard } from '@/components/tasks/TaskCard'
import { SubTaskList } from '@/components/tasks/SubTaskList'
import { listPhaseTasks, createPhaseTask } from '@/api/phases'
import { addAssignee } from '@/api/tasks'
import { useAuthStore } from '@/store/authStore'
import type { Task } from '@/types'

interface PhaseTaskListProps {
  phaseId: string
  phaseStatus: 'pending' | 'active' | 'completed'
  onTaskClick: (task: Task) => void
}

// PhaseTaskList — Section 10.4 / 10.5:
// Flat task list for a phase. "Add task" inline row at bottom (no modal).
// Read-only if phase is not active.
export function PhaseTaskList({ phaseId, phaseStatus, onTaskClick }: PhaseTaskListProps) {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const currentUser = useAuthStore((s) => s.user)

  // Inline add-task form state
  const [adding, setAdding] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newDueDate, setNewDueDate] = useState('')
  const [saving, setSaving] = useState(false)

  const fetchTasks = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await listPhaseTasks(phaseId)
      // Only top-level tasks (parent_task_id === null) appear in the list
      setTasks(data.filter((t) => t.parent_task_id === null))
    } catch {
      setError('Failed to load tasks.')
    } finally {
      setLoading(false)
    }
  }, [phaseId])

  useEffect(() => {
    void fetchTasks()
  }, [fetchTasks])

  async function handleAddTask(e: React.FormEvent) {
    e.preventDefault()
    const title = newTitle.trim()
    if (!title) return

    setSaving(true)
    try {
      const task = await createPhaseTask(phaseId, {
        title,
        due_date: newDueDate || undefined,
      })

      // Auto-assign to the creating user as a default so the task appears in My Tasks.
      // The assignee picker (to change/add others) is deferred — needs GET /users endpoint.
      if (currentUser) {
        await addAssignee(task.id, currentUser.id)
        // Optimistically update the task's assignee_ids in local state
        task.assignee_ids = [currentUser.id]
      }

      setTasks((prev) => [...prev, task])
      setNewTitle('')
      setNewDueDate('')
      setAdding(false)
    } catch {
      // Silently fail — user can retry
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12 text-text-secondary">
        <Loader2 size={20} className="animate-spin" />
      </div>
    )
  }

  if (error) {
    return <p className="py-6 text-center text-md text-status-red">{error}</p>
  }

  return (
    <div className="flex flex-col gap-2">
      {tasks.length === 0 && !adding && (
        <div className="flex flex-col items-center py-10 text-text-secondary gap-1">
          <p className="text-md font-medium text-text-primary">No tasks yet</p>
          <p className="text-md">
            {phaseStatus === 'active'
              ? 'Add the first task below.'
              : 'Tasks will appear when this phase is active.'}
          </p>
        </div>
      )}

      {tasks.map((task) => (
        <div key={task.id}>
          <TaskCard task={task} onClick={() => onTaskClick(task)} />
          <SubTaskList
            subTasks={task.sub_tasks}
            onSubTaskClick={() => {
              // Sub-task click — open parent task slide-over so full context is available
              onTaskClick(task)
            }}
          />
        </div>
      ))}

      {/* Inline add-task row — only on active phases */}
      {phaseStatus === 'active' && (
        <div className="mt-2">
          {adding ? (
            <form onSubmit={(e) => void handleAddTask(e)} className="flex flex-col gap-2">
              <div className="flex items-center gap-2">
                <input
                  autoFocus
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="Task title…"
                  className="flex-1 border border-border-default rounded-sm px-3 py-2 text-md bg-bg-surface focus:outline-none focus:border-border-strong focus:ring-2 focus:ring-brand-light"
                  disabled={saving}
                />
                <input
                  type="date"
                  value={newDueDate}
                  onChange={(e) => setNewDueDate(e.target.value)}
                  title="Due date (optional)"
                  className="border border-border-default rounded-sm px-3 py-2 text-md bg-bg-surface focus:outline-none focus:border-border-strong focus:ring-2 focus:ring-brand-light"
                  disabled={saving}
                />
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="submit"
                  disabled={saving || !newTitle.trim()}
                  className="px-4 py-2 bg-brand text-white text-md font-medium rounded-md hover:bg-brand-hover disabled:opacity-50 transition-colors"
                >
                  {saving ? <Loader2 size={14} className="animate-spin" /> : 'Add task'}
                </button>
                <button
                  type="button"
                  onClick={() => { setAdding(false); setNewTitle(''); setNewDueDate('') }}
                  className="px-3 py-2 border border-border-default text-md text-text-primary rounded-md hover:bg-bg-subtle transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          ) : (
            <button
              onClick={() => setAdding(true)}
              className="flex items-center gap-2 w-full px-4 py-2.5 border border-dashed border-border-default rounded-md text-md text-text-secondary hover:border-brand hover:text-brand hover:bg-brand-light transition-colors"
            >
              <Plus size={15} />
              Add task
            </button>
          )}
        </div>
      )}
    </div>
  )
}
