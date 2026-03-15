import { apiGet, apiPost, apiPut, apiDelete } from './client'
import type { Project, ProjectStatus } from '@/types'

export interface ProjectCreate {
  name: string
  customer_name: string
  description?: string
  start_date?: string
  target_end_date?: string
  owner_id?: string
}

export interface ProjectUpdate {
  name?: string
  customer_name?: string
  description?: string
  status?: ProjectStatus
  start_date?: string
  target_end_date?: string
  actual_end_date?: string
  owner_id?: string
}

export interface ProjectFilters {
  status?: ProjectStatus
  owner_id?: string
  skip?: number
  limit?: number
}

export function listProjects(filters?: ProjectFilters): Promise<Project[]> {
  return apiGet<Project[]>('/projects', filters as Record<string, unknown>)
}

export function getProject(id: string): Promise<Project> {
  return apiGet<Project>(`/projects/${id}`)
}

export function createProject(payload: ProjectCreate): Promise<Project> {
  return apiPost<Project>('/projects', payload)
}

export function updateProject(id: string, payload: ProjectUpdate): Promise<Project> {
  return apiPut<Project>(`/projects/${id}`, payload)
}

export function deleteProject(id: string): Promise<void> {
  return apiDelete(`/projects/${id}`)
}
