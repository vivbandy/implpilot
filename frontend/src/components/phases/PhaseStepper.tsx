import { Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Phase } from '@/types'

interface PhaseStepperProps {
  phases: Phase[]
  // The phase whose tasks are currently shown — not necessarily the active phase
  selectedPhaseId: string | null
  onPhaseClick: (phase: Phase) => void
}

// PhaseStepper — Section 10.4:
// Horizontal row of 4 steps.
// Circle: empty=gray (pending), brand-filled (active), status-green-filled+checkmark (completed).
// Label: text-secondary (pending), text-primary (active/completed).
// Connector: gray (pending→pending), brand (completed→active), status-green (completed→completed).
// Pending phases are not clickable.
export function PhaseStepper({ phases, selectedPhaseId, onPhaseClick }: PhaseStepperProps) {
  const sorted = [...phases].sort((a, b) => a.order - b.order)

  return (
    <div className="flex items-center px-6 py-4 bg-bg-surface border-b border-border-default">
      {sorted.map((phase, idx) => {
        const isCompleted = phase.status === 'completed'
        const isActive = phase.status === 'active'
        const isPending = phase.status === 'pending'
        const isSelected = phase.id === selectedPhaseId
        const isClickable = isCompleted || isActive

        return (
          <div key={phase.id} className="flex items-center flex-1">
            {/* Step */}
            <button
              onClick={() => isClickable && onPhaseClick(phase)}
              disabled={isPending}
              className={cn(
                'flex flex-col items-center gap-1 min-w-0',
                isClickable ? 'cursor-pointer' : 'cursor-default'
              )}
            >
              {/* Circle indicator */}
              <div
                className={cn(
                  'w-6 h-6 rounded-full flex items-center justify-center shrink-0 ring-2 ring-offset-1',
                  isCompleted && 'bg-status-green ring-status-green',
                  isActive && 'bg-brand ring-brand',
                  isPending && 'bg-bg-subtle ring-border-default',
                  isSelected && !isPending && 'ring-offset-2'
                )}
              >
                {isCompleted && <Check size={12} className="text-white" strokeWidth={3} />}
                {isActive && <span className="w-2 h-2 rounded-full bg-white" />}
              </div>

              {/* Label */}
              <span
                className={cn(
                  'text-sm whitespace-nowrap',
                  isPending ? 'text-text-secondary' : 'text-text-primary',
                  isSelected && 'font-semibold'
                )}
              >
                {phase.display_name}
              </span>

              {/* Task count chip */}
              {phase.task_count !== undefined && (
                <span className="text-xs text-text-secondary">
                  {phase.completed_task_count ?? 0}/{phase.task_count} tasks
                </span>
              )}
            </button>

            {/* Connector line — not shown after last step */}
            {idx < sorted.length - 1 && (
              <div className="flex-1 mx-2 h-px mt-[-20px]">
                <div
                  className={cn(
                    'h-full',
                    // If this phase is completed, color the connector leading to next
                    isCompleted ? 'bg-status-green' : 'bg-border-default'
                  )}
                />
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
