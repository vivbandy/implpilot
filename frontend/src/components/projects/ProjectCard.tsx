import { useNavigate } from 'react-router-dom'
import { HealthSpectrumBar } from '@/components/shared/HealthSpectrumBar'
import { StatusPill } from '@/components/shared/StatusPill'
import { cn } from '@/lib/utils'
import type { Project } from '@/types'

interface ProjectCardProps {
  project: Project
}

// ProjectCard — Section 10.5 Dashboard:
// customer name (12px secondary), project name (16px semibold),
// health spectrum bar (full width, sm size), task completion micro-bar,
// days remaining badge, phase indicator.
export function ProjectCard({ project }: ProjectCardProps) {
  const navigate = useNavigate()
  const daysRemaining = getDaysRemaining(project.target_end_date)

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => navigate(`/projects/${project.id}`)}
      onKeyDown={(e) => e.key === 'Enter' && navigate(`/projects/${project.id}`)}
      className="bg-bg-surface border border-border-default rounded-md shadow-card p-4 cursor-pointer hover:border-brand transition-colors flex flex-col gap-3"
    >
      {/* Customer name */}
      <p className="text-sm text-text-secondary truncate">{project.customer_name}</p>

      {/* Project name + status pill */}
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-lg font-semibold text-text-primary leading-tight line-clamp-2">
          {project.name}
        </h3>
        <div className="shrink-0">
          <StatusPill status={project.status} />
        </div>
      </div>

      {/* Health spectrum bar */}
      <HealthSpectrumBar
        score={project.health_score ?? 0}
        size="sm"
        showLabel
        showScore
      />

      {/* Footer row: phase + days remaining */}
      <div className="flex items-center justify-between pt-1 border-t border-border-default">
        <span className="text-sm text-text-secondary capitalize">
          Phase: <span className="text-text-primary font-medium">{project.current_phase}</span>
        </span>
        {daysRemaining !== null && (
          <span
            className={cn(
              'text-sm font-medium',
              daysRemaining < 0
                ? 'text-status-red'
                : daysRemaining <= 7
                ? 'text-status-yellow'
                : 'text-text-secondary'
            )}
          >
            {daysRemaining < 0
              ? `${Math.abs(daysRemaining)}d overdue`
              : daysRemaining === 0
              ? 'Due today'
              : `${daysRemaining}d left`}
          </span>
        )}
      </div>
    </div>
  )
}

function getDaysRemaining(targetDate: string | null): number | null {
  if (!targetDate) return null
  const diff = new Date(targetDate).getTime() - Date.now()
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
}
