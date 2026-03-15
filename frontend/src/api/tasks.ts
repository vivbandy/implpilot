import { apiGet, apiPost, apiPut, apiDelete } from './client'
import type { Task, SubTask } from '@/types'

export interface TaskUpdate {
  title?: string
  description?: string
  status?: 'not_started' | 'in_progress' | 'blocked' | 'completed' | 'cancelled'
  priority?: 'low' | 'medium' | 'high' | 'critical'
  due_date?: string
  start_date?: string
  matrix_quadrant?: 'do' | 'schedule' | 'delegate' | 'eliminate'
  matrix_override?: boolean
  order?: number
}

export interface SubTaskCreate {
  title: string
  description?: string
  priority?: 'low' | 'medium' | 'high' | 'critical'
  due_date?: string
  start_date?: string
  order?: number
}

export function getTask(taskId: string): Promise<Task> {
  return apiGet<Task>(`/tasks/${taskId}`)
}

export function updateTask(taskId: string, payload: TaskUpdate): Promise<Task> {
  return apiPut<Task>(`/tasks/${taskId}`, payload)
}

export function deleteTask(taskId: string): Promise<void> {
  return apiDelete(`/tasks/${taskId}`)
}

export function createSubTask(taskId: string, payload: SubTaskCreate): Promise<SubTask> {
  return apiPost<SubTask>(`/tasks/${taskId}/subtasks`, payload)
}

// Dashboard My Tasks — all top-level tasks assigned to the current user except cancelled
export function getMyTasks(): Promise<Task[]> {
  return apiGet<Task[]>('/tasks/my-tasks')
}
