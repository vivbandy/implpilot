import { cn } from '@/lib/utils'
import { PriorityDot } from '@/components/shared/PriorityDot'
import { StatusPill } from '@/components/shared/StatusPill'
import type { Task, SubTask } from '@/types'

interface TaskCardProps {
  task: Task | SubTask
  isSubTask?: boolean
  onClick?: () => void
}

// TaskCard — Section 10.4:
// bg-surface border-default radius-md shadow-card, padding 12px 16px
// Left: priority dot | Center: title + sub-info row | Right: status pill
// Overdue: left border 3px status-red
// Blocked: left border 3px status-yellow
// Sub-task: 24px left indent, no shadow, lighter border
export function TaskCard({ task, isSubTask = false, onClick }: TaskCardProps) {
  const isOverdue =
    task.due_date != null &&
    new Date(task.due_date) < new Date() &&
    task.status !== 'completed' &&
    task.status !== 'cancelled'

  const isBlocked = task.status === 'blocked'

  return (
    <div
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onClick={onClick}
      onKeyDown={(e) => e.key === 'Enter' && onClick?.()}
      className={cn(
        'flex items-start gap-3 px-4 py-3 bg-bg-surface border border-border-default rounded-md',
        !isSubTask && 'shadow-card',
        isSubTask && 'ml-6 border-border-default/60 shadow-none',
        isOverdue && 'border-l-4 border-l-status-red',
        isBlocked && !isOverdue && 'border-l-4 border-l-status-yellow',
        onClick && 'cursor-pointer hover:bg-bg-subtle transition-colors'
      )}
    >
      {/* Priority dot */}
      <div className="pt-0.5 shrink-0">
        <PriorityDot priority={task.priority} />
      </div>

      {/* Center: title + meta row */}
      <div className="flex-1 min-w-0">
        <p className="text-md font-medium text-text-primary truncate">{task.title}</p>
        <div className="flex items-center gap-3 mt-1 flex-wrap">
          {task.due_date && (
            <span className={cn('text-sm', isOverdue ? 'text-status-red' : 'text-text-secondary')}>
              Due {formatDate(task.due_date)}
            </span>
          )}
          {/* Sub-task count badge — only on top-level tasks */}
          {'sub_tasks' in task && task.sub_tasks.length > 0 && (
            <span className="text-sm text-text-secondary">
              {task.sub_tasks.filter((s) => s.status === 'completed').length}/{task.sub_tasks.length} sub-tasks
            </span>
          )}
        </div>
      </div>

      {/* Status pill */}
      <div className="shrink-0 pt-0.5">
        <StatusPill status={task.status} />
      </div>
    </div>
  )
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}
