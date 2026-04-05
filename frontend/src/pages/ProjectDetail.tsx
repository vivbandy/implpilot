import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Loader2 } from 'lucide-react'
import { PhaseStepper } from '@/components/phases/PhaseStepper'
import { PhaseTaskList } from '@/components/phases/PhaseTaskList'
import { TaskDetailSlideOver } from '@/components/tasks/TaskDetailSlideOver'
import { StatusPill } from '@/components/shared/StatusPill'
import { HealthSpectrumBar } from '@/components/shared/HealthSpectrumBar'
import { getProject } from '@/api/projects'
import { listFeatureRequests, listEscalations, listContacts } from '@/api/related'
import type { Project, Phase, Task, FeatureRequest, Escalation, Contact } from '@/types'
import { cn } from '@/lib/utils'

type TabId = 'tasks' | 'feature_requests' | 'escalations' | 'contacts' | 'notes' | 'reports'

const TABS: { id: TabId; label: string }[] = [
  { id: 'tasks', label: 'Tasks' },
  { id: 'feature_requests', label: 'Feature Requests' },
  { id: 'escalations', label: 'Escalations' },
  { id: 'contacts', label: 'Contacts' },
  { id: 'notes', label: 'Notes' },
  { id: 'reports', label: 'Reports' },
]

export default function ProjectDetail() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()

  const [project, setProject] = useState<Project | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<TabId>('tasks')

  // Selected phase for task list — defaults to the project's current_phase
  const [selectedPhaseId, setSelectedPhaseId] = useState<string | null>(null)

  // Task slide-over state
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)
  const [slideOverOpen, setSlideOverOpen] = useState(false)

  // Related object data for tabs
  const [featureRequests, setFeatureRequests] = useState<FeatureRequest[]>([])
  const [escalations, setEscalations] = useState<Escalation[]>([])
  const [contacts, setContacts] = useState<Contact[]>([])

  const fetchProject = useCallback(async () => {
    if (!projectId) return
    try {
      const data = await getProject(projectId)
      setProject(data)
      // Default selected phase to the active phase
      if (data.phases) {
        const activePhase = data.phases.find((p) => p.status === 'active')
        if (activePhase) setSelectedPhaseId(activePhase.id)
        else if (data.phases.length > 0) setSelectedPhaseId(data.phases[0].id)
      }
    } catch {
      // Project not found — redirect
      navigate('/projects')
    } finally {
      setLoading(false)
    }
  }, [projectId, navigate])

  useEffect(() => {
    void fetchProject()
  }, [fetchProject])

  // Lazy-load related objects when tabs are opened
  useEffect(() => {
    if (!projectId) return
    if (activeTab === 'feature_requests' && featureRequests.length === 0) {
      void listFeatureRequests(projectId).then(setFeatureRequests)
    }
    if (activeTab === 'escalations' && escalations.length === 0) {
      void listEscalations(projectId).then(setEscalations)
    }
    if (activeTab === 'contacts' && contacts.length === 0) {
      void listContacts(projectId).then(setContacts)
    }
  }, [activeTab, projectId, featureRequests.length, escalations.length, contacts.length])

  function handleTaskClick(task: Task) {
    setSelectedTask(task)
    setSlideOverOpen(true)
  }

  function handleTaskUpdated(updated: Task) {
    setSelectedTask(updated)
  }

  function handlePhaseClick(phase: Phase) {
    setSelectedPhaseId(phase.id)
    setActiveTab('tasks')
  }

  if (loading || !project) {
    return (
      <div className="flex items-center justify-center h-full text-text-secondary">
        <Loader2 size={24} className="animate-spin" />
      </div>
    )
  }

  const phases = project.phases ?? []
  const selectedPhase = phases.find((p) => p.id === selectedPhaseId) ?? null

  return (
    <div className="flex flex-col h-full">
      {/* Page header */}
      <header className="h-14 bg-bg-surface border-b border-border-default flex items-center gap-3 px-6 shrink-0">
        <button
          onClick={() => navigate('/projects')}
          className="p-1.5 rounded-md text-text-secondary hover:bg-bg-subtle transition-colors"
        >
          <ArrowLeft size={16} />
        </button>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-semibold text-text-primary truncate">{project.name}</h1>
            <StatusPill status={project.status} />
          </div>
          <p className="text-sm text-text-secondary truncate">{project.customer_name}</p>
        </div>
        {/* Health score in header */}
        <div className="shrink-0 w-32">
          <HealthSpectrumBar score={project.health_score ?? 0} size="sm" showLabel showScore />
        </div>
      </header>

      {/* PhaseStepper — pinned below header, always visible (Section 10.5) */}
      {phases.length > 0 && (
        <PhaseStepper
          phases={phases}
          selectedPhaseId={selectedPhaseId}
          onPhaseClick={handlePhaseClick}
        />
      )}

      {/* Tab row */}
      <div className="bg-bg-surface border-b border-border-default px-6 shrink-0">
        <div className="flex gap-0">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'px-4 py-3 text-md transition-colors border-b-2 -mb-px',
                activeTab === tab.id
                  ? 'text-brand font-semibold border-brand'
                  : 'text-text-secondary border-transparent hover:text-text-primary hover:border-border-default'
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto px-6 py-6 max-w-screen-lg">
        {activeTab === 'tasks' && (
          <>
            {selectedPhase ? (
              <PhaseTaskList
                phaseId={selectedPhase.id}
                phaseStatus={selectedPhase.status}
                onTaskClick={handleTaskClick}
              />
            ) : (
              <p className="text-md text-text-secondary py-6">No phases found for this project.</p>
            )}
          </>
        )}

        {activeTab === 'feature_requests' && (
          <FeatureRequestsTab featureRequests={featureRequests} />
        )}

        {activeTab === 'escalations' && (
          <EscalationsTab escalations={escalations} />
        )}

        {activeTab === 'contacts' && (
          <ContactsTab contacts={contacts} />
        )}

        {activeTab === 'notes' && (
          <div className="flex flex-col items-center py-12 text-text-secondary gap-1">
            <p className="text-md font-medium text-text-primary">Project-level notes</p>
            <p className="text-md">Add notes to individual tasks via the task slide-over.</p>
          </div>
        )}

        {activeTab === 'reports' && (
          <div className="flex flex-col items-center py-12 text-text-secondary gap-1">
            <p className="text-md font-medium text-text-primary">Reports</p>
            <p className="text-md">Report builder coming in Step 10.</p>
          </div>
        )}
      </div>

      {/* Task detail slide-over */}
      <TaskDetailSlideOver
        task={selectedTask}
        projectId={project.id}
        open={slideOverOpen}
        onClose={() => setSlideOverOpen(false)}
        onTaskUpdated={handleTaskUpdated}
      />
    </div>
  )
}

// ─── Tab sub-components ───────────────────────────────────────────────────────

function FeatureRequestsTab({ featureRequests }: { featureRequests: FeatureRequest[] }) {
  if (featureRequests.length === 0) {
    return (
      <div className="flex flex-col items-center py-12 text-text-secondary gap-1">
        <p className="text-md font-medium text-text-primary">No feature requests</p>
        <p className="text-md">Feature requests appear here when created manually or via #tags in notes.</p>
      </div>
    )
  }
  return (
    <div className="flex flex-col gap-2">
      {featureRequests.map((fr) => (
        <div key={fr.id} className="bg-bg-surface border border-border-default rounded-md px-4 py-3 shadow-card">
          <div className="flex items-start justify-between gap-2">
            <p className="text-md font-medium text-text-primary">{fr.title}</p>
            <StatusPill status={fr.status as 'active'} />
          </div>
          {fr.description && (
            <p className="text-sm text-text-secondary mt-1 line-clamp-2">{fr.description}</p>
          )}
          <p className="text-sm text-text-secondary mt-1 capitalize">
            {fr.priority} priority · {fr.source === 'tag_derived' ? 'Auto-created from tag' : 'Manual'}
          </p>
        </div>
      ))}
    </div>
  )
}

function EscalationsTab({ escalations }: { escalations: Escalation[] }) {
  if (escalations.length === 0) {
    return (
      <div className="flex flex-col items-center py-12 text-text-secondary gap-1">
        <p className="text-md font-medium text-text-primary">No escalations</p>
        <p className="text-md">Escalations appear here when created manually or via #tags in notes.</p>
      </div>
    )
  }
  return (
    <div className="flex flex-col gap-2">
      {escalations.map((esc) => (
        <div key={esc.id} className="bg-bg-surface border border-border-default rounded-md px-4 py-3 shadow-card">
          <div className="flex items-start justify-between gap-2">
            <p className="text-md font-medium text-text-primary">{esc.title}</p>
            <span className={cn(
              'text-xs font-medium px-2 py-0.5 rounded-pill',
              esc.severity === 'critical' && 'bg-status-red-bg text-status-red',
              esc.severity === 'high' && 'bg-status-yellow-bg text-status-yellow',
              esc.severity === 'medium' && 'bg-status-purple-bg text-status-purple',
              esc.severity === 'low' && 'bg-status-gray-bg text-status-gray',
            )}>
              {esc.severity}
            </span>
          </div>
          {esc.description && (
            <p className="text-sm text-text-secondary mt-1 line-clamp-2">{esc.description}</p>
          )}
          <p className="text-sm text-text-secondary mt-1 capitalize">
            {esc.status.replace('_', ' ')} · {esc.source === 'tag_derived' ? 'Auto-created from tag' : 'Manual'}
          </p>
        </div>
      ))}
    </div>
  )
}

function ContactsTab({ contacts }: { contacts: Contact[] }) {
  if (contacts.length === 0) {
    return (
      <div className="flex flex-col items-center py-12 text-text-secondary gap-1">
        <p className="text-md font-medium text-text-primary">No contacts</p>
        <p className="text-md">Add contacts to track key stakeholders for this project.</p>
      </div>
    )
  }
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      {contacts.map((c) => (
        <div key={c.id} className="bg-bg-surface border border-border-default rounded-md px-4 py-3 shadow-card">
          <div className="flex items-center gap-2">
            <p className="text-md font-medium text-text-primary">{c.name}</p>
            {c.is_primary && (
              <span className="text-xs font-medium px-2 py-0.5 rounded-pill bg-brand-light text-brand">
                Primary
              </span>
            )}
          </div>
          {c.role && <p className="text-sm text-text-secondary">{c.role}</p>}
          {c.email && (
            <a href={`mailto:${c.email}`} className="text-sm text-brand hover:underline">
              {c.email}
            </a>
          )}
        </div>
      ))}
    </div>
  )
}
