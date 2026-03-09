import { cn } from '@/lib/utils'
import type { TaskPriority } from '@/types'

interface PriorityDotProps {
  priority: TaskPriority
  className?: string
  // Show label alongside the dot — useful in detail views
  showLabel?: boolean
}

// PriorityDot — Section 10.4:
// 8px colored circle shown next to task title.
// Uses priority token colors — never hardcoded hex.
export function PriorityDot({ priority, className, showLabel = false }: PriorityDotProps) {
  return (
    <span className={cn('inline-flex items-center gap-1.5 shrink-0', className)}>
      <span
        className={cn('inline-block w-2 h-2 rounded-full shrink-0', DOT_COLORS[priority])}
        title={PRIORITY_LABELS[priority]}
      />
      {showLabel && (
        <span className="text-xs text-text-secondary">{PRIORITY_LABELS[priority]}</span>
      )}
    </span>
  )
}

const DOT_COLORS: Record<TaskPriority, string> = {
  critical: 'bg-priority-critical',
  high:     'bg-priority-high',
  medium:   'bg-priority-medium',
  low:      'bg-priority-low',
}

const PRIORITY_LABELS: Record<TaskPriority, string> = {
  critical: 'Critical',
  high:     'High',
  medium:   'Medium',
  low:      'Low',
}
