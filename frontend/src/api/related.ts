import { apiGet, apiPost, apiDelete } from './client'
import type { FeatureRequest, Escalation, Contact } from '@/types'

// ─── Feature Requests ─────────────────────────────────────────────────────────

export function listFeatureRequests(projectId: string): Promise<FeatureRequest[]> {
  return apiGet<FeatureRequest[]>(`/projects/${projectId}/feature-requests`)
}

export interface FeatureRequestCreate {
  title: string
  description?: string
  why_important?: string
  priority?: 'low' | 'medium' | 'high' | 'critical'
  phase_id?: string
  requested_by?: string
}

export function createFeatureRequest(
  projectId: string,
  payload: FeatureRequestCreate
): Promise<FeatureRequest> {
  return apiPost<FeatureRequest>(`/projects/${projectId}/feature-requests`, payload)
}

// ─── Escalations ──────────────────────────────────────────────────────────────

export function listEscalations(projectId: string): Promise<Escalation[]> {
  return apiGet<Escalation[]>(`/projects/${projectId}/escalations`)
}

export interface EscalationCreate {
  title: string
  description?: string
  severity?: 'low' | 'medium' | 'high' | 'critical'
  phase_id?: string
  raised_by?: string
}

export function createEscalation(
  projectId: string,
  payload: EscalationCreate
): Promise<Escalation> {
  return apiPost<Escalation>(`/projects/${projectId}/escalations`, payload)
}

// ─── Contacts ─────────────────────────────────────────────────────────────────

export function listContacts(projectId: string): Promise<Contact[]> {
  return apiGet<Contact[]>(`/projects/${projectId}/contacts`)
}

export interface ContactCreate {
  name: string
  email?: string
  role?: string
  company?: string
  is_primary?: boolean
}

export function createContact(projectId: string, payload: ContactCreate): Promise<Contact> {
  return apiPost<Contact>(`/projects/${projectId}/contacts`, payload)
}

export function deleteContact(contactId: string): Promise<void> {
  return apiDelete(`/contacts/${contactId}`)
}
