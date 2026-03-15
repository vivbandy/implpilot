import { apiGet, apiPost, apiDelete } from './client'
import type { Note, NoteCreate, NoteEntityType, ExternalTicket, ExternalTicketCreate, ExternalTicketEntityType } from '@/types'

// ─── Notes ────────────────────────────────────────────────────────────────────

export function listNotes(entityType: NoteEntityType, entityId: string): Promise<Note[]> {
  return apiGet<Note[]>('/notes', {
    entity_type: entityType,
    entity_id: entityId,
  } as Record<string, unknown>)
}

export function createNote(payload: NoteCreate): Promise<Note> {
  return apiPost<Note>('/notes', payload)
}

export function deleteNote(noteId: string): Promise<void> {
  return apiDelete(`/notes/${noteId}`)
}

// ─── External Tickets ─────────────────────────────────────────────────────────

export function listExternalTickets(
  entityType: ExternalTicketEntityType,
  entityId: string
): Promise<ExternalTicket[]> {
  return apiGet<ExternalTicket[]>('/external-tickets', {
    entity_type: entityType,
    entity_id: entityId,
  } as Record<string, unknown>)
}

export function createExternalTicket(payload: ExternalTicketCreate): Promise<ExternalTicket> {
  return apiPost<ExternalTicket>('/external-tickets', payload)
}

export function deleteExternalTicket(ticketId: string): Promise<void> {
  return apiDelete(`/external-tickets/${ticketId}`)
}
