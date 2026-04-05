import { cn } from '@/lib/utils'
import type { TaskStatus, PhaseStatus, ProjectStatus } from '@/types'

// All possible statuses across tasks, phases, and projects
type AnyStatus = TaskStatus | PhaseStatus | ProjectStatus

interface StatusPillProps {
  status: AnyStatus
  className?: string
}

// StatusPill — Section 10.4:
// Pill shape (radius-pill), 12px medium.
// Background is the -bg token variant; text is the full color.
// Maps every status value from tasks and phases.
export function StatusPill({ status, className }: StatusPillProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded-pill text-xs font-medium whitespace-nowrap',
        STATUS_STYLES[status],
        className
      )}
    >
      {STATUS_LABELS[status]}
    </span>
  )
}

const STATUS_STYLES: Record<AnyStatus, string> = {
  // Task statuses
  not_started: 'bg-status-purple-bg text-status-purple',
  in_progress:  'bg-status-yellow-bg text-status-yellow',
  blocked:      'bg-status-red-bg text-status-red',
  completed:    'bg-status-green-bg text-status-green',
  cancelled:    'bg-status-gray-bg text-status-gray',

  // Phase statuses
  pending:  'bg-status-gray-bg text-status-gray',
  active:   'bg-status-yellow-bg text-status-yellow',

  // Project-specific statuses
  at_risk:  'bg-status-red-bg text-status-red',
  on_hold:  'bg-status-gray-bg text-status-gray',
}

const STATUS_LABELS: Record<AnyStatus, string> = {
  not_started: 'Not started',
  in_progress:  'In progress',
  blocked:      'Blocked',
  completed:    'Completed',
  cancelled:    'Cancelled',
  pending:      'Pending',
  active:       'Active',
  at_risk:      'At Risk',
  on_hold:      'On Hold',
}
