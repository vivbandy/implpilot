import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { TaskCard } from './TaskCard'
import type { SubTask } from '@/types'

interface SubTaskListProps {
  subTasks: SubTask[]
  onSubTaskClick?: (subTask: SubTask) => void
}

// SubTaskList — collapses under a parent task with a chevron toggle.
// Section 10.4: sub-task indent 24px, lighter border, no shadow.
export function SubTaskList({ subTasks, onSubTaskClick }: SubTaskListProps) {
  const [expanded, setExpanded] = useState(false)

  if (subTasks.length === 0) return null

  const completedCount = subTasks.filter((s) => s.status === 'completed').length

  return (
    <div className="mt-1">
      <button
        onClick={() => setExpanded((v) => !v)}
        className="flex items-center gap-1.5 ml-6 text-sm text-text-secondary hover:text-text-primary transition-colors"
      >
        {expanded ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
        <span>
          {subTasks.length} sub-task{subTasks.length !== 1 ? 's' : ''} · {completedCount} done
        </span>
      </button>

      {expanded && (
        <div className="mt-1 flex flex-col gap-1">
          {subTasks.map((st) => (
            <TaskCard
              key={st.id}
              task={st}
              isSubTask
              onClick={onSubTaskClick ? () => onSubTaskClick(st) : undefined}
            />
          ))}
        </div>
      )}
    </div>
  )
}
