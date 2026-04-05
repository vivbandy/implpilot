import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Loader2, Search } from 'lucide-react'
import { StatusPill } from '@/components/shared/StatusPill'
import { HealthSpectrumBar } from '@/components/shared/HealthSpectrumBar'
import { QuickCreateProjectModal } from '@/components/projects/QuickCreateProjectModal'
import { listProjects } from '@/api/projects'
import type { Project, ProjectStatus } from '@/types'

const STATUS_FILTERS: { label: string; value: ProjectStatus | 'all' }[] = [
  { label: 'All', value: 'all' },
  { label: 'Active', value: 'active' },
  { label: 'At Risk', value: 'at_risk' },
  { label: 'On Hold', value: 'on_hold' },
  { label: 'Completed', value: 'completed' },
  { label: 'Cancelled', value: 'cancelled' },
]

export default function Projects() {
  const navigate = useNavigate()
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<ProjectStatus | 'all'>('all')
  const [search, setSearch] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)

  useEffect(() => {
    setLoading(true)
    void listProjects({ limit: 100 })
      .then(setProjects)
      .finally(() => setLoading(false))
  }, [])

  const filtered = projects.filter((p) => {
    const matchesStatus = statusFilter === 'all' || p.status === statusFilter
    const matchesSearch =
      !search ||
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.customer_name.toLowerCase().includes(search.toLowerCase())
    return matchesStatus && matchesSearch
  })

  function handleCreated(project: Project) {
    setShowCreateModal(false)
    navigate(`/projects/${project.id}`)
  }

  return (
    <div>
      {/* Page header */}
      <header className="h-14 bg-bg-surface border-b border-border-default flex items-center justify-between px-6">
        <h1 className="text-xl font-semibold text-text-primary">Projects</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-brand text-white text-md font-medium rounded-md hover:bg-brand-hover transition-colors"
        >
          <Plus size={15} />
          New Project
        </button>
      </header>

      <div className="px-6 py-6 max-w-screen-xl mx-auto">
        {/* Filter bar */}
        <div className="flex items-center gap-3 mb-5 flex-wrap">
          {/* Search */}
          <div className="relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search projects…"
              className="pl-8 pr-3 py-2 border border-border-default rounded-sm text-md bg-bg-surface focus:outline-none focus:border-border-strong focus:ring-2 focus:ring-brand-light w-56"
            />
          </div>

          {/* Status filter buttons */}
          <div className="flex items-center gap-1 flex-wrap">
            {STATUS_FILTERS.map((f) => (
              <button
                key={f.value}
                onClick={() => setStatusFilter(f.value)}
                className={`px-3 py-1.5 rounded-md text-md transition-colors ${
                  statusFilter === f.value
                    ? 'bg-brand text-white'
                    : 'text-text-secondary hover:bg-bg-subtle hover:text-text-primary'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        {loading ? (
          <div className="flex items-center justify-center py-16 text-text-secondary">
            <Loader2 size={20} className="animate-spin" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center py-16 text-text-secondary gap-1">
            <p className="text-md font-medium text-text-primary">
              {projects.length === 0 ? 'No projects yet' : 'No projects match your filters'}
            </p>
            {projects.length === 0 && (
              <button
                onClick={() => setShowCreateModal(true)}
                className="mt-2 text-brand hover:underline text-md"
              >
                Create your first project
              </button>
            )}
          </div>
        ) : (
          <div className="bg-bg-surface border border-border-default rounded-md overflow-hidden shadow-card">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border-default bg-bg-subtle">
                  <th className="text-left px-4 py-2.5 text-sm font-semibold text-text-secondary uppercase tracking-wide">
                    Project
                  </th>
                  <th className="text-left px-4 py-2.5 text-sm font-semibold text-text-secondary uppercase tracking-wide">
                    Status
                  </th>
                  <th className="text-left px-4 py-2.5 text-sm font-semibold text-text-secondary uppercase tracking-wide w-40">
                    Health
                  </th>
                  <th className="text-left px-4 py-2.5 text-sm font-semibold text-text-secondary uppercase tracking-wide">
                    Phase
                  </th>
                  <th className="text-left px-4 py-2.5 text-sm font-semibold text-text-secondary uppercase tracking-wide">
                    Target End
                  </th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((project) => (
                  <tr
                    key={project.id}
                    onClick={() => navigate(`/projects/${project.id}`)}
                    className="border-b border-border-default last:border-0 cursor-pointer hover:bg-bg-subtle transition-colors"
                  >
                    <td className="px-4 py-3">
                      <p className="text-md font-medium text-text-primary">{project.name}</p>
                      <p className="text-sm text-text-secondary">{project.customer_name}</p>
                    </td>
                    <td className="px-4 py-3">
                      <StatusPill status={project.status} />
                    </td>
                    <td className="px-4 py-3 w-40">
                      <HealthSpectrumBar score={project.health_score ?? 0} size="sm" showScore />
                    </td>
                    <td className="px-4 py-3 text-md text-text-primary capitalize">
                      {project.current_phase}
                    </td>
                    <td className="px-4 py-3 text-md text-text-secondary">
                      {project.target_end_date
                        ? new Date(project.target_end_date).toLocaleDateString('en-US', {
                            month: 'short', day: 'numeric', year: 'numeric',
                          })
                        : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <QuickCreateProjectModal
        open={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreated={handleCreated}
      />
    </div>
  )
}
