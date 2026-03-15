import { useState, useEffect, useCallback } from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { X, Plus, ExternalLink, Loader2 } from 'lucide-react'
import { StatusPill } from '@/components/shared/StatusPill'
import { PriorityDot } from '@/components/shared/PriorityDot'
import { TagChip } from '@/components/shared/TagChip'
import { SubTaskList } from './SubTaskList'
import { updateTask } from '@/api/tasks'
import { listNotes, createNote, listExternalTickets } from '@/api/notes'
import type { Task, Note, ExternalTicket } from '@/types'

interface TaskDetailSlideOverProps {
  task: Task | null
  projectId: string
  open: boolean
  onClose: () => void
  onTaskUpdated: (updated: Task) => void
}

// TaskDetailSlideOver — opens from right edge, Section 10.4 slide-over pattern.
// Uses @radix-ui/react-dialog for focus trap + keyboard dismiss.
// Shows: title, status, priority, description, sub-tasks, external tickets, notes.
export function TaskDetailSlideOver({
  task,
  projectId,
  open,
  onClose,
  onTaskUpdated,
}: TaskDetailSlideOverProps) {
  const [notes, setNotes] = useState<Note[]>([])
  const [tickets, setTickets] = useState<ExternalTicket[]>([])
  const [loadingNotes, setLoadingNotes] = useState(false)
  const [newNoteContent, setNewNoteContent] = useState('')
  const [savingNote, setSavingNote] = useState(false)

  const loadTaskData = useCallback(async (taskId: string) => {
    setLoadingNotes(true)
    try {
      const [fetchedNotes, fetchedTickets] = await Promise.all([
        listNotes('task', taskId),
        listExternalTickets('task', taskId),
      ])
      setNotes(fetchedNotes)
      setTickets(fetchedTickets)
    } catch {
      // Non-blocking — notes section shows empty state
    } finally {
      setLoadingNotes(false)
    }
  }, [])

  useEffect(() => {
    if (open && task) {
      void loadTaskData(task.id)
    } else {
      setNotes([])
      setTickets([])
      setNewNoteContent('')
    }
  }, [open, task, loadTaskData])

  async function handleStatusChange(status: Task['status']) {
    if (!task) return
    try {
      const updated = await updateTask(task.id, { status })
      onTaskUpdated(updated)
    } catch {
      // Silently fail — user sees no change
    }
  }

  async function handleAddNote(e: React.FormEvent) {
    e.preventDefault()
    if (!task || !newNoteContent.trim()) return

    setSavingNote(true)
    try {
      const note = await createNote({
        entity_type: 'task',
        entity_id: task.id,
        content: newNoteContent.trim(),
        project_id: projectId,
      })
      setNotes((prev) => [note, ...prev])
      setNewNoteContent('')
    } catch {
      // Silently fail
    } finally {
      setSavingNote(false)
    }
  }

  if (!task) return null

  const isOverdue =
    task.due_date != null &&
    new Date(task.due_date) < new Date() &&
    task.status !== 'completed' &&
    task.status !== 'cancelled'

  return (
    <Dialog.Root open={open} onOpenChange={(v) => !v && onClose()}>
      <Dialog.Portal>
        {/* Backdrop */}
        <Dialog.Overlay className="fixed inset-0 bg-black/20 z-40" />

        {/* Slide-over panel — right edge */}
        <Dialog.Content
          className="fixed inset-y-0 right-0 z-50 w-full max-w-lg bg-bg-overlay shadow-modal flex flex-col focus:outline-none"
          aria-label="Task detail"
        >
          {/* Header */}
          <div className="flex items-start justify-between px-6 py-4 border-b border-border-default shrink-0">
            <div className="flex-1 min-w-0 pr-4">
              <div className="flex items-center gap-2 mb-1">
                <PriorityDot priority={task.priority} />
                <StatusPill status={task.status} />
                {isOverdue && (
                  <span className="text-xs font-medium text-status-red">Overdue</span>
                )}
              </div>
              <Dialog.Title className="text-lg font-semibold text-text-primary">
                {task.title}
              </Dialog.Title>
            </div>
            <Dialog.Close
              onClick={onClose}
              className="p-1.5 rounded-md text-text-secondary hover:bg-bg-subtle hover:text-text-primary transition-colors shrink-0"
            >
              <X size={16} />
            </Dialog.Close>
          </div>

          {/* Body — scrollable */}
          <div className="flex-1 overflow-y-auto px-6 py-5 space-y-6">

            {/* Description */}
            {task.description && (
              <section>
                <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wide mb-2">
                  Description
                </h3>
                <p className="text-md text-text-primary whitespace-pre-wrap">{task.description}</p>
              </section>
            )}

            {/* Dates */}
            {(task.due_date || task.start_date) && (
              <section>
                <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wide mb-2">
                  Dates
                </h3>
                <div className="flex gap-6 text-md text-text-primary">
                  {task.start_date && <span>Start: {formatDate(task.start_date)}</span>}
                  {task.due_date && (
                    <span className={isOverdue ? 'text-status-red' : ''}>
                      Due: {formatDate(task.due_date)}
                    </span>
                  )}
                </div>
              </section>
            )}

            {/* Status changer */}
            <section>
              <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wide mb-2">
                Status
              </h3>
              <div className="flex flex-wrap gap-2">
                {(['not_started', 'in_progress', 'blocked', 'completed'] as const).map((s) => (
                  <button
                    key={s}
                    onClick={() => void handleStatusChange(s)}
                    className={
                      task.status === s
                        ? 'opacity-100'
                        : 'opacity-50 hover:opacity-80 transition-opacity'
                    }
                  >
                    <StatusPill status={s} />
                  </button>
                ))}
              </div>
            </section>

            {/* Sub-tasks */}
            {task.sub_tasks.length > 0 && (
              <section>
                <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wide mb-2">
                  Sub-tasks ({task.sub_tasks.filter((s) => s.status === 'completed').length}/
                  {task.sub_tasks.length})
                </h3>
                <SubTaskList subTasks={task.sub_tasks} />
              </section>
            )}

            {/* External tickets */}
            {tickets.length > 0 && (
              <section>
                <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wide mb-2">
                  External Tickets
                </h3>
                <div className="flex flex-col gap-2">
                  {tickets.map((t) => (
                    <a
                      key={t.id}
                      href={t.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 text-md text-brand hover:underline"
                    >
                      <ExternalLink size={13} className="shrink-0" />
                      <span>{t.label ?? t.ticket_id ?? t.url}</span>
                      <span className="text-sm text-text-secondary capitalize">{t.ticket_system}</span>
                    </a>
                  ))}
                </div>
              </section>
            )}

            {/* Notes */}
            <section>
              <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wide mb-2">
                Notes
              </h3>

              {/* Add note form */}
              <form onSubmit={(e) => void handleAddNote(e)} className="mb-4">
                <textarea
                  value={newNoteContent}
                  onChange={(e) => setNewNoteContent(e.target.value)}
                  placeholder="Add a note… (supports #tags for auto-actions)"
                  rows={3}
                  className="w-full border border-border-default rounded-sm px-3 py-2 text-md bg-bg-surface resize-none focus:outline-none focus:border-border-strong focus:ring-2 focus:ring-brand-light"
                />
                <button
                  type="submit"
                  disabled={savingNote || !newNoteContent.trim()}
                  className="mt-2 flex items-center gap-2 px-3 py-1.5 bg-brand text-white text-md font-medium rounded-md hover:bg-brand-hover disabled:opacity-50 transition-colors"
                >
                  {savingNote ? <Loader2 size={13} className="animate-spin" /> : <Plus size={13} />}
                  Add note
                </button>
              </form>

              {loadingNotes ? (
                <div className="flex items-center justify-center py-4 text-text-secondary">
                  <Loader2 size={16} className="animate-spin" />
                </div>
              ) : notes.length === 0 ? (
                <p className="text-md text-text-secondary">No notes yet.</p>
              ) : (
                <div className="flex flex-col gap-3">
                  {notes.map((note) => (
                    <div
                      key={note.id}
                      className="bg-bg-subtle rounded-md px-4 py-3 border border-border-default"
                    >
                      <p className="text-md text-text-primary whitespace-pre-wrap">{note.content}</p>
                      <p className="text-sm text-text-secondary mt-1">{formatDateTime(note.created_at)}</p>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function formatDateTime(dateStr: string): string {
  return new Date(dateStr).toLocaleString('en-US', {
    month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit',
  })
}
