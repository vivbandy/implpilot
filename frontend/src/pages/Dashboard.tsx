import { useState, useEffect } from 'react'
import { Bell, Loader2 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { ProjectCard } from '@/components/projects/ProjectCard'
import { StatusPill } from '@/components/shared/StatusPill'
import { PriorityDot } from '@/components/shared/PriorityDot'
import { TaskDetailSlideOver } from '@/components/tasks/TaskDetailSlideOver'
import { listProjects } from '@/api/projects'
import { getMyTasks } from '@/api/tasks'
import type { Project, Task } from '@/types'

export default function Dashboard() {
  const navigate = useNavigate()
  const [projects, setProjects] = useState<Project[]>([])
  const [myTasks, setMyTasks] = useState<Task[]>([])
  const [loadingProjects, setLoadingProjects] = useState(true)
  const [loadingTasks, setLoadingTasks] = useState(true)

  // Task slide-over — opens when a My Tasks row is clicked
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)
  const [slideOverOpen, setSlideOverOpen] = useState(false)

  useEffect(() => {
    void listProjects({ limit: 50 })
      .then(setProjects)
      .finally(() => setLoadingProjects(false))

    void getMyTasks()
      .then(setMyTasks)
      .finally(() => setLoadingTasks(false))
  }, [])

  function handleTaskClick(task: Task) {
    setSelectedTask(task)
    setSlideOverOpen(true)
  }

  function handleTaskUpdated(updated: Task) {
    setSelectedTask(updated)
    setMyTasks((prev) => prev.map((t) => (t.id === updated.id ? updated : t)))
  }

  const activeProjects = projects.filter((p) => p.status !== 'completed' && p.status !== 'cancelled')
  const completedProjects = projects.filter((p) => p.status === 'completed' || p.status === 'cancelled')

  return (
    <div>
      {/* Page header */}
      <header className="h-14 bg-bg-surface border-b border-border-default flex items-center justify-between px-6">
        <h1 className="text-xl font-semibold text-text-primary">Dashboard</h1>
        {/* Notification bell — static placeholder, wired in Step 11 */}
        <button
          title="Notifications (coming soon)"
          className="p-2 rounded-md text-text-secondary hover:bg-bg-subtle hover:text-text-primary transition-colors"
        >
          <Bell size={18} />
        </button>
      </header>

      <div className="px-6 py-6 max-w-screen-xl mx-auto space-y-8">

        {/* Active Projects — 3-col grid */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-text-primary">
              Active Projects
              {!loadingProjects && (
                <span className="ml-2 text-md font-normal text-text-secondary">
                  ({activeProjects.length})
                </span>
              )}
            </h2>
            <button
              onClick={() => navigate('/projects')}
              className="text-md text-brand hover:underline"
            >
              View all
            </button>
          </div>

          {loadingProjects ? (
            <div className="flex items-center justify-center py-12 text-text-secondary">
              <Loader2 size={20} className="animate-spin" />
            </div>
          ) : activeProjects.length === 0 ? (
            <div className="flex flex-col items-center py-12 text-text-secondary gap-1">
              <p className="text-md font-medium text-text-primary">No active projects</p>
              <p className="text-md">
                <button
                  onClick={() => navigate('/projects')}
                  className="text-brand hover:underline"
                >
                  Create your first project
                </button>
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {activeProjects.map((p) => (
                <ProjectCard key={p.id} project={p} />
              ))}
            </div>
          )}
        </section>

        {/* My Tasks table */}
        <section>
          <h2 className="text-lg font-semibold text-text-primary mb-4">My Tasks</h2>

          {loadingTasks ? (
            <div className="flex items-center justify-center py-8 text-text-secondary">
              <Loader2 size={20} className="animate-spin" />
            </div>
          ) : myTasks.length === 0 ? (
            <div className="bg-bg-surface border border-border-default rounded-md p-8 text-center">
              <p className="text-md font-medium text-text-primary">No tasks assigned to you</p>
              <p className="text-md text-text-secondary mt-1">
                Tasks assigned to you across all projects appear here.
              </p>
            </div>
          ) : (
            <div className="bg-bg-surface border border-border-default rounded-md overflow-hidden shadow-card">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border-default bg-bg-subtle">
                    <th className="text-left px-4 py-2.5 text-sm font-semibold text-text-secondary uppercase tracking-wide">
                      Task
                    </th>
                    <th className="text-left px-4 py-2.5 text-sm font-semibold text-text-secondary uppercase tracking-wide">
                      Priority
                    </th>
                    <th className="text-left px-4 py-2.5 text-sm font-semibold text-text-secondary uppercase tracking-wide">
                      Status
                    </th>
                    <th className="text-left px-4 py-2.5 text-sm font-semibold text-text-secondary uppercase tracking-wide">
                      Due
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {myTasks.map((task, idx) => {
                    const isOverdue =
                      task.due_date != null &&
                      new Date(task.due_date) < new Date() &&
                      task.status !== 'completed' &&
                      task.status !== 'cancelled'

                    return (
                      <tr
                        key={task.id}
                        onClick={() => handleTaskClick(task)}
                        className={`border-b border-border-default last:border-0 cursor-pointer hover:bg-bg-subtle transition-colors ${
                          idx % 2 === 0 ? '' : 'bg-bg-app/50'
                        }`}
                      >
                        <td className="px-4 py-3 text-md text-text-primary max-w-xs truncate">
                          {task.title}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1.5">
                            <PriorityDot priority={task.priority} />
                            <span className="text-sm text-text-secondary capitalize">
                              {task.priority}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <StatusPill status={task.status} />
                        </td>
                        <td className={`px-4 py-3 text-md ${isOverdue ? 'text-status-red' : 'text-text-secondary'}`}>
                          {task.due_date ? formatDate(task.due_date) : '—'}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* Completed/Cancelled projects */}
        {completedProjects.length > 0 && (
          <section>
            <h2 className="text-lg font-semibold text-text-secondary mb-4">
              Completed &amp; Cancelled ({completedProjects.length})
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {completedProjects.map((p) => (
                <ProjectCard key={p.id} project={p} />
              ))}
            </div>
          </section>
        )}
      </div>

      {/* Task slide-over — project_id is on every task response */}
      <TaskDetailSlideOver
        task={selectedTask}
        projectId={selectedTask?.project_id ?? ''}
        open={slideOverOpen}
        onClose={() => setSlideOverOpen(false)}
        onTaskUpdated={handleTaskUpdated}
      />
    </div>
  )
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}
