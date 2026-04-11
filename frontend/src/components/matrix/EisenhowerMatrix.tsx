/**
 * EisenhowerMatrix — 4-quadrant drag-and-drop task prioritisation board.
 *
 * Layout (2×2 grid):
 *
 *               URGENT          NOT URGENT
 *   IMPORTANT  [ Do ]          [ Schedule ]
 *   NOT IMP.   [ Delegate ]    [ Eliminate ]
 *
 * Drag logic:
 *   - Each quadrant is a DndKit droppable zone.
 *   - Dragging a card to a new quadrant calls PUT /tasks/{id} with
 *     { matrix_quadrant: <new>, matrix_override: true }
 *     so manual moves are never overwritten by auto-classification.
 *
 * Unclassified tasks (matrix_quadrant === null) appear in a holding row
 * above the grid. Dragging them into a quadrant classifies them.
 */

import { useState, useCallback } from 'react'
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  useDroppable,
  useDraggable,
  type DragEndEvent,
  type DragStartEvent,
} from '@dnd-kit/core'
import { CSS } from '@dnd-kit/utilities'
import { Loader2, HelpCircle, Info } from 'lucide-react'
import * as Tooltip from '@radix-ui/react-tooltip'
import { cn } from '@/lib/utils'
import { PriorityDot } from '@/components/shared/PriorityDot'
import { StatusPill } from '@/components/shared/StatusPill'
import { updateTask } from '@/api/tasks'
import type { Task, MatrixQuadrant } from '@/types'

// ─── Quadrant metadata ────────────────────────────────────────────────────────

interface QuadrantMeta {
  id: MatrixQuadrant
  label: string
  tagline: string
  /** Tailwind bg class for the quadrant header strip */
  headerBg: string
  /** Tailwind border-left class for draggable cards in this quadrant */
  accentBorder: string
}

// Colors stay within existing design tokens — no new hex values.
const QUADRANTS: QuadrantMeta[] = [
  {
    id: 'do',
    label: 'Do',
    tagline: 'Urgent + Important',
    headerBg: 'bg-status-red/10',
    accentBorder: 'border-l-status-red',
  },
  {
    id: 'schedule',
    label: 'Schedule',
    tagline: 'Not Urgent + Important',
    headerBg: 'bg-brand/10',
    accentBorder: 'border-l-brand',
  },
  {
    id: 'delegate',
    label: 'Delegate',
    tagline: 'Urgent + Not Important',
    headerBg: 'bg-status-yellow/10',
    accentBorder: 'border-l-status-yellow',
  },
  {
    id: 'eliminate',
    label: 'Eliminate',
    tagline: 'Not Urgent + Not Important',
    headerBg: 'bg-status-gray/10',
    accentBorder: 'border-l-status-gray',
  },
]

// ─── Props ────────────────────────────────────────────────────────────────────

interface EisenhowerMatrixProps {
  tasks: Task[]
  loading: boolean
  onTasksChange: (tasks: Task[]) => void
  onTaskClick: (task: Task) => void
}

// ─── Draggable card ───────────────────────────────────────────────────────────

interface DraggableCardProps {
  task: Task
  accentBorder: string
  onClick: () => void
  isDragging?: boolean
}

function DraggableCard({ task, accentBorder, onClick, isDragging = false }: DraggableCardProps) {
  const { attributes, listeners, setNodeRef, transform } = useDraggable({ id: task.id })

  const isOverdue =
    task.due_date != null &&
    new Date(task.due_date) < new Date() &&
    task.status !== 'completed' &&
    task.status !== 'cancelled'

  const style = transform
    ? { transform: CSS.Translate.toString(transform) }
    : undefined

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      className={cn(
        'flex items-start gap-2.5 px-3 py-2.5 bg-bg-surface border border-border-default rounded-md shadow-card',
        'border-l-4 cursor-grab active:cursor-grabbing select-none',
        isOverdue ? 'border-l-status-red' : accentBorder,
        isDragging && 'opacity-40',
      )}
    >
      {/* Priority dot */}
      <div className="pt-0.5 shrink-0">
        <PriorityDot priority={task.priority} />
      </div>

      {/* Title + meta */}
      <div
        className="flex-1 min-w-0"
        onClick={(e) => {
          // Allow click-to-open only when not dragging
          e.stopPropagation()
          onClick()
        }}
      >
        <p className="text-sm font-medium text-text-primary leading-snug line-clamp-2">
          {task.title}
        </p>
        <div className="flex items-center gap-2 mt-1 flex-wrap">
          {task.due_date && (
            <span className={cn('text-xs', isOverdue ? 'text-status-red' : 'text-text-secondary')}>
              {formatDate(task.due_date)}
            </span>
          )}
          {task.matrix_override && (
            <span className="text-xs text-text-disabled italic">manual</span>
          )}
        </div>
      </div>

      {/* Status pill — shrink-0 so it never wraps under title */}
      <div className="shrink-0 pt-0.5">
        <StatusPill status={task.status} />
      </div>
    </div>
  )
}

// ─── Overlay card (shown while dragging) ─────────────────────────────────────

function OverlayCard({ task }: { task: Task }) {
  const isOverdue =
    task.due_date != null &&
    new Date(task.due_date) < new Date() &&
    task.status !== 'completed' &&
    task.status !== 'cancelled'

  return (
    <div className={cn(
      'flex items-start gap-2.5 px-3 py-2.5 bg-bg-surface border border-border-default rounded-md shadow-modal',
      'border-l-4 cursor-grabbing opacity-95 rotate-1',
      isOverdue ? 'border-l-status-red' : 'border-l-brand',
    )}>
      <div className="pt-0.5 shrink-0">
        <PriorityDot priority={task.priority} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-text-primary leading-snug line-clamp-2">
          {task.title}
        </p>
      </div>
      <div className="shrink-0 pt-0.5">
        <StatusPill status={task.status} />
      </div>
    </div>
  )
}

// ─── Droppable quadrant column ────────────────────────────────────────────────

interface QuadrantColumnProps {
  meta: QuadrantMeta
  tasks: Task[]
  activeTaskId: string | null
  onTaskClick: (task: Task) => void
}

function QuadrantColumn({ meta, tasks, activeTaskId, onTaskClick }: QuadrantColumnProps) {
  const { isOver, setNodeRef } = useDroppable({ id: meta.id })

  return (
    <div
      ref={setNodeRef}
      className={cn(
        'flex flex-col rounded-md border border-border-default bg-bg-surface overflow-hidden',
        'transition-colors',
        isOver && 'ring-2 ring-brand ring-offset-1',
      )}
    >
      {/* Quadrant header */}
      <div className={cn('px-3 py-2.5', meta.headerBg)}>
        <p className="text-sm font-semibold text-text-primary">{meta.label}</p>
        <p className="text-xs text-text-secondary mt-0.5">{meta.tagline}</p>
      </div>

      {/* Task list */}
      <div className="flex flex-col gap-2 p-2 flex-1 min-h-[120px]">
        {tasks.length === 0 && !isOver && (
          <p className="text-xs text-text-disabled text-center mt-4">Drop tasks here</p>
        )}
        {tasks.map((task) => (
          <DraggableCard
            key={task.id}
            task={task}
            accentBorder={meta.accentBorder}
            onClick={() => onTaskClick(task)}
            isDragging={task.id === activeTaskId}
          />
        ))}
      </div>
    </div>
  )
}

// ─── Unclassified holding area ────────────────────────────────────────────────

interface UnclassifiedAreaProps {
  tasks: Task[]
  activeTaskId: string | null
  onTaskClick: (task: Task) => void
}

function UnclassifiedArea({ tasks, activeTaskId, onTaskClick }: UnclassifiedAreaProps) {
  const { isOver, setNodeRef } = useDroppable({ id: 'unclassified' })

  if (tasks.length === 0) return null

  return (
    <div
      ref={setNodeRef}
      className={cn(
        'rounded-md border border-border-default bg-bg-subtle p-3 mb-4',
        isOver && 'ring-2 ring-brand ring-offset-1',
      )}
    >
      <div className="flex items-center gap-1.5 mb-2">
        <HelpCircle size={14} className="text-text-secondary" />
        <p className="text-sm font-medium text-text-secondary">
          Unclassified ({tasks.length})
        </p>
        <span className="text-xs text-text-disabled ml-1">— drag into a quadrant to classify</span>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
        {tasks.map((task) => (
          <DraggableCard
            key={task.id}
            task={task}
            accentBorder="border-l-border-default"
            onClick={() => onTaskClick(task)}
            isDragging={task.id === activeTaskId}
          />
        ))}
      </div>
    </div>
  )
}

// ─── Classification legend ────────────────────────────────────────────────────

/**
 * Explains the auto-classification rules so users know how to influence
 * which quadrant a task lands in without manual drag overrides.
 *
 * Design decision (Option A): overdue date alone does NOT make a task
 * important — only priority=high/critical or status=blocked does.
 * Users should set priority explicitly to control importance.
 */
function ClassificationLegend() {
  return (
    <Tooltip.Provider delayDuration={200}>
      <div className="flex items-center gap-2 mb-4">
        <p className="text-sm text-text-secondary">
          Tasks are auto-classified by urgency and importance.
        </p>
        <Tooltip.Root>
          <Tooltip.Trigger asChild>
            <button
              className="text-text-disabled hover:text-text-secondary transition-colors"
              aria-label="How classification works"
            >
              <Info size={15} />
            </button>
          </Tooltip.Trigger>
          <Tooltip.Portal>
            <Tooltip.Content
              side="bottom"
              align="start"
              sideOffset={6}
              className="z-50 max-w-sm rounded-md bg-bg-surface border border-border-default shadow-popover p-4 text-sm text-text-primary"
            >
              <p className="font-semibold mb-2">How tasks are classified</p>

              <p className="font-medium text-text-secondary uppercase tracking-wide text-xs mb-1">
                Urgent — any of:
              </p>
              <ul className="list-disc list-inside space-y-0.5 text-text-secondary mb-3">
                <li>Due date is today, overdue, or within 3 days</li>
                <li>Status is <span className="text-text-primary font-medium">Blocked</span></li>
                <li>Priority is <span className="text-text-primary font-medium">Critical</span></li>
              </ul>

              <p className="font-medium text-text-secondary uppercase tracking-wide text-xs mb-1">
                Important — any of:
              </p>
              <ul className="list-disc list-inside space-y-0.5 text-text-secondary mb-3">
                <li>Priority is <span className="text-text-primary font-medium">High</span> or <span className="text-text-primary font-medium">Critical</span></li>
                <li>Status is <span className="text-text-primary font-medium">Blocked</span></li>
              </ul>

              <p className="text-text-secondary text-xs border-t border-border-default pt-2 mt-1">
                To land in <strong className="text-text-primary">Do</strong>, a task must be both urgent <em>and</em> important — set priority to High or Critical. An overdue task with Medium priority lands in <strong className="text-text-primary">Delegate</strong> because it is urgent but not marked important.
                <br /><br />
                Drag any card to override its quadrant manually.
              </p>
              <Tooltip.Arrow className="fill-border-default" />
            </Tooltip.Content>
          </Tooltip.Portal>
        </Tooltip.Root>
      </div>
    </Tooltip.Provider>
  )
}

// ─── Main component ───────────────────────────────────────────────────────────

export function EisenhowerMatrix({ tasks, loading, onTasksChange, onTaskClick }: EisenhowerMatrixProps) {
  const [activeTask, setActiveTask] = useState<Task | null>(null)
  const [optimisticTasks, setOptimisticTasks] = useState<Task[] | null>(null)

  // The displayed task list — use optimistic state if present, else prop
  const displayTasks = optimisticTasks ?? tasks

  // Use pointer sensor with a small activation distance to prevent accidental drags
  // when the user just wants to click to open the slide-over.
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
  )

  function handleDragStart(event: DragStartEvent) {
    const task = displayTasks.find((t) => t.id === event.active.id)
    setActiveTask(task ?? null)
  }

  const handleDragEnd = useCallback(async (event: DragEndEvent) => {
    setActiveTask(null)
    const { active, over } = event
    if (!over) return

    const taskId = active.id as string
    const newQuadrant = over.id as MatrixQuadrant | 'unclassified'

    // Find the dragged task
    const task = displayTasks.find((t) => t.id === taskId)
    if (!task) return

    // Dropping onto 'unclassified' clears the quadrant
    const resolvedQuadrant = newQuadrant === 'unclassified' ? null : newQuadrant

    // No-op: same quadrant
    if (task.matrix_quadrant === resolvedQuadrant) return

    // Optimistic update — reflect the change immediately in the UI
    const updated = displayTasks.map((t) =>
      t.id === taskId
        ? { ...t, matrix_quadrant: resolvedQuadrant, matrix_override: resolvedQuadrant !== null }
        : t,
    )
    setOptimisticTasks(updated)
    onTasksChange(updated)

    try {
      const savedTask = await updateTask(taskId, {
        matrix_quadrant: resolvedQuadrant ?? undefined,
        matrix_override: resolvedQuadrant !== null,
      })
      // Reconcile with the server response
      setOptimisticTasks((prev) =>
        prev ? prev.map((t) => (t.id === taskId ? { ...t, ...savedTask } : t)) : null,
      )
      onTasksChange(
        (optimisticTasks ?? tasks).map((t) => (t.id === taskId ? { ...t, ...savedTask } : t)),
      )
    } catch {
      // Roll back on error
      setOptimisticTasks(null)
      onTasksChange(tasks)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [displayTasks, tasks, onTasksChange])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16 text-text-secondary">
        <Loader2 size={20} className="animate-spin" />
      </div>
    )
  }

  if (tasks.length === 0) {
    return (
      <div className="flex flex-col items-center py-16 text-text-secondary gap-1">
        <p className="text-sm font-medium text-text-primary">No tasks in your matrix</p>
        <p className="text-sm">Tasks assigned to you will appear here once created.</p>
      </div>
    )
  }

  // Partition tasks by quadrant
  const byQuadrant = (q: MatrixQuadrant | null) =>
    displayTasks.filter((t) => t.matrix_quadrant === q)

  return (
    <DndContext sensors={sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
      {/* Classification rules legend */}
      <ClassificationLegend />

      {/* Unclassified holding area */}
      <UnclassifiedArea
        tasks={byQuadrant(null)}
        activeTaskId={activeTask?.id ?? null}
        onTaskClick={onTaskClick}
      />

      {/* 2×2 quadrant grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {QUADRANTS.map((meta) => (
          <QuadrantColumn
            key={meta.id}
            meta={meta}
            tasks={byQuadrant(meta.id)}
            activeTaskId={activeTask?.id ?? null}
            onTaskClick={onTaskClick}
          />
        ))}
      </div>

      {/* Floating overlay card — follows the pointer while dragging */}
      <DragOverlay>
        {activeTask ? <OverlayCard task={activeTask} /> : null}
      </DragOverlay>
    </DndContext>
  )
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}
