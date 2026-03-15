import { useState } from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { X, Loader2 } from 'lucide-react'
import { createProject } from '@/api/projects'
import type { Project } from '@/types'

interface QuickCreateProjectModalProps {
  open: boolean
  onClose: () => void
  onCreated: (project: Project) => void
}

// QuickCreateProjectModal — minimal form: name + customer_name + optional dates.
// Uses @radix-ui/react-dialog (already installed). Section 10.4 modal styles.
export function QuickCreateProjectModal({ open, onClose, onCreated }: QuickCreateProjectModalProps) {
  const [form, setForm] = useState({
    name: '',
    customer_name: '',
    start_date: '',
    target_end_date: '',
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.name.trim() || !form.customer_name.trim()) return

    setSaving(true)
    setError(null)
    try {
      const project = await createProject({
        name: form.name.trim(),
        customer_name: form.customer_name.trim(),
        start_date: form.start_date || undefined,
        target_end_date: form.target_end_date || undefined,
      })
      onCreated(project)
      setForm({ name: '', customer_name: '', start_date: '', target_end_date: '' })
    } catch {
      setError('Failed to create project. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  function handleClose() {
    if (saving) return
    setForm({ name: '', customer_name: '', start_date: '', target_end_date: '' })
    setError(null)
    onClose()
  }

  return (
    <Dialog.Root open={open} onOpenChange={(v) => !v && handleClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/20 z-40" />
        <Dialog.Content
          className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-md bg-bg-overlay rounded-lg shadow-modal p-6 focus:outline-none"
          aria-label="Create project"
        >
          <div className="flex items-center justify-between mb-5">
            <Dialog.Title className="text-xl font-semibold text-text-primary">
              New Project
            </Dialog.Title>
            <Dialog.Close
              onClick={handleClose}
              className="p-1.5 rounded-md text-text-secondary hover:bg-bg-subtle transition-colors"
            >
              <X size={16} />
            </Dialog.Close>
          </div>

          <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-text-secondary mb-1">
                Project name <span className="text-status-red">*</span>
              </label>
              <input
                name="name"
                type="text"
                value={form.name}
                onChange={handleChange}
                required
                autoFocus
                placeholder="e.g. Acme Corp Onboarding"
                className="w-full border border-border-default rounded-sm px-3 py-2 text-md bg-bg-surface focus:outline-none focus:border-border-strong focus:ring-2 focus:ring-brand-light"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-text-secondary mb-1">
                Customer name <span className="text-status-red">*</span>
              </label>
              <input
                name="customer_name"
                type="text"
                value={form.customer_name}
                onChange={handleChange}
                required
                placeholder="e.g. Acme Corp"
                className="w-full border border-border-default rounded-sm px-3 py-2 text-md bg-bg-surface focus:outline-none focus:border-border-strong focus:ring-2 focus:ring-brand-light"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-semibold text-text-secondary mb-1">
                  Start date
                </label>
                <input
                  name="start_date"
                  type="date"
                  value={form.start_date}
                  onChange={handleChange}
                  className="w-full border border-border-default rounded-sm px-3 py-2 text-md bg-bg-surface focus:outline-none focus:border-border-strong focus:ring-2 focus:ring-brand-light"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-text-secondary mb-1">
                  Target end date
                </label>
                <input
                  name="target_end_date"
                  type="date"
                  value={form.target_end_date}
                  onChange={handleChange}
                  className="w-full border border-border-default rounded-sm px-3 py-2 text-md bg-bg-surface focus:outline-none focus:border-border-strong focus:ring-2 focus:ring-brand-light"
                />
              </div>
            </div>

            {error && <p className="text-md text-status-red">{error}</p>}

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={handleClose}
                disabled={saving}
                className="px-4 py-2 border border-border-default text-md text-text-primary rounded-md hover:bg-bg-subtle transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={saving || !form.name.trim() || !form.customer_name.trim()}
                className="flex items-center gap-2 px-4 py-2 bg-brand text-white text-md font-medium rounded-md hover:bg-brand-hover disabled:opacity-50 transition-colors"
              >
                {saving && <Loader2 size={14} className="animate-spin" />}
                Create project
              </button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
