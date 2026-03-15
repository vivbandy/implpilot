// ─── Shared TypeScript types — mirrors backend Pydantic schemas ───
// Keep in sync with backend response shapes. No `any` types per spec.

export type UserRole = 'admin' | 'lead' | 'viewer'

export interface User {
  id: string
  email: string
  username: string
  full_name: string | null
  role: UserRole
  is_active: boolean
  created_at: string
  updated_at: string
}

// ─── Projects ────────────────────────────────────────────────────

export type ProjectStatus = 'active' | 'at_risk' | 'on_hold' | 'completed' | 'cancelled'
export type PhaseName = 'kickoff' | 'design' | 'implement' | 'deploy'

export interface Project {
  id: string
  name: string
  customer_name: string
  description: string | null
  status: ProjectStatus
  health_score: number | null
  current_phase: PhaseName
  start_date: string | null
  target_end_date: string | null
  actual_end_date: string | null
  owner_id: string
  created_by: string
  created_at: string
  updated_at: string
  phases?: Phase[]
}

// ─── Phases ──────────────────────────────────────────────────────

export type PhaseStatus = 'pending' | 'active' | 'completed'

export interface Phase {
  id: string
  project_id: string
  name: PhaseName
  display_name: string
  order: number
  status: PhaseStatus
  start_date: string | null
  target_end_date: string | null
  completed_at: string | null
  description: string | null
  created_at: string
  updated_at: string
  task_count?: number
  completed_task_count?: number
}

// ─── Tasks ───────────────────────────────────────────────────────

export type TaskStatus = 'not_started' | 'in_progress' | 'blocked' | 'completed' | 'cancelled'
export type TaskPriority = 'low' | 'medium' | 'high' | 'critical'
export type MatrixQuadrant = 'do' | 'schedule' | 'delegate' | 'eliminate'

export interface SubTask {
  id: string
  project_id: string
  phase_id: string
  parent_task_id: string
  title: string
  description: string | null
  status: TaskStatus
  priority: TaskPriority
  start_date: string | null
  due_date: string | null
  completed_at: string | null
  matrix_quadrant: MatrixQuadrant | null
  matrix_override: boolean
  order: number
  created_by: string | null
  created_at: string
  updated_at: string
  assignee_ids: string[]
}

export interface Task {
  id: string
  project_id: string
  phase_id: string
  parent_task_id: string | null
  title: string
  description: string | null
  status: TaskStatus
  priority: TaskPriority
  start_date: string | null
  due_date: string | null
  completed_at: string | null
  matrix_quadrant: MatrixQuadrant | null
  matrix_override: boolean
  order: number
  created_by: string | null
  created_at: string
  updated_at: string
  assignee_ids: string[]
  sub_tasks: SubTask[]
}

// ─── Tags ────────────────────────────────────────────────────────

export type TagCategory = 'escalation' | 'feature_request' | 'sentiment' | 'custom'
export type TagSentiment = 'negative' | 'neutral' | 'positive'
export type TagAutoAction = 'create_escalation' | 'create_feature_request' | 'none'

export interface TagDefinition {
  id: string
  name: string
  category: TagCategory
  sentiment: TagSentiment | null
  auto_action: TagAutoAction
  description: string | null
  color: string | null
  created_at: string
}

// ─── Related Objects ─────────────────────────────────────────────

export type FeatureRequestStatus = 'open' | 'under_review' | 'planned' | 'shipped' | 'declined'
export type EscalationStatus = 'open' | 'in_progress' | 'resolved' | 'closed'
export type EscalationSeverity = 'low' | 'medium' | 'high' | 'critical'

export interface FeatureRequest {
  id: string
  project_id: string
  phase_id: string | null
  task_id: string | null
  title: string
  description: string | null
  why_important: string | null
  priority: TaskPriority
  status: FeatureRequestStatus
  requested_by: string | null
  source: 'manual' | 'tag_derived'
  source_note_id: string | null
  created_by: string | null
  created_at: string
  updated_at: string
}

export interface Escalation {
  id: string
  project_id: string
  phase_id: string | null
  task_id: string | null
  title: string
  description: string | null
  severity: EscalationSeverity
  status: EscalationStatus
  raised_by: string | null
  source: 'manual' | 'tag_derived'
  source_note_id: string | null
  resolved_at: string | null
  created_by: string | null
  created_at: string
  updated_at: string
}

export interface Contact {
  id: string
  project_id: string
  name: string
  email: string | null
  role: string | null
  company: string | null
  is_primary: boolean
  created_at: string
}

// ─── Notes ───────────────────────────────────────────────────────

export type NoteEntityType = 'project' | 'phase' | 'task' | 'feature_request' | 'escalation'

export interface Note {
  id: string
  entity_type: NoteEntityType
  entity_id: string
  content: string
  author_id: string | null
  created_at: string
  updated_at: string
}

export interface NoteCreate {
  entity_type: NoteEntityType
  entity_id: string
  content: string
  project_id: string
}

// ─── External Tickets ────────────────────────────────────────────

export type ExternalTicketEntityType = 'task' | 'feature_request' | 'escalation'
export type ExternalTicketSystem = 'jira' | 'zendesk' | 'other'

export interface ExternalTicket {
  id: string
  entity_type: ExternalTicketEntityType
  entity_id: string
  ticket_system: ExternalTicketSystem
  ticket_id: string | null
  url: string
  label: string | null
  status_cache: string | null
  last_synced_at: string | null
  created_at: string
}

export interface ExternalTicketCreate {
  entity_type: ExternalTicketEntityType
  entity_id: string
  ticket_system: ExternalTicketSystem
  ticket_id?: string
  url: string
  label?: string
}

// ─── Auth ────────────────────────────────────────────────────────

export interface AuthTokenResponse {
  access_token: string
  token_type: string
}

export interface LoginCredentials {
  email: string
  password: string
}

// ─── API error shape ─────────────────────────────────────────────

export interface ApiError {
  detail: string
}
