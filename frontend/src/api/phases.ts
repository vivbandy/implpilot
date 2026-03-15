import { apiGet, apiPost, apiPut } from './client'
import type { Phase, Task } from '@/types'

export function listPhases(projectId: string): Promise<Phase[]> {
  return apiGet<Phase[]>(`/phases/projects/${projectId}/phases`)
}

export function getPhase(phaseId: string): Promise<Phase> {
  return apiGet<Phase>(`/phases/${phaseId}`)
}

export interface PhaseUpdate {
  description?: string
  start_date?: string
  target_end_date?: string
}

export function updatePhase(phaseId: string, payload: PhaseUpdate): Promise<Phase> {
  return apiPut<Phase>(`/phases/${phaseId}`, payload)
}

export function completePhase(phaseId: string): Promise<Phase> {
  return apiPost<Phase>(`/phases/${phaseId}/complete`)
}

export function listPhaseTasks(phaseId: string): Promise<Task[]> {
  return apiGet<Task[]>(`/phases/${phaseId}/tasks`)
}

export interface TaskCreate {
  title: string
  description?: string
  priority?: 'low' | 'medium' | 'high' | 'critical'
  due_date?: string
  start_date?: string
  order?: number
}

export function createPhaseTask(phaseId: string, payload: TaskCreate): Promise<Task> {
  return apiPost<Task>(`/phases/${phaseId}/tasks`, payload)
}
