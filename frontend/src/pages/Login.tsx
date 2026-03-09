import { useState, useEffect, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'

// Login page — Section 10.5:
// Centered 480px card on bg-app background.
// No background image or gradient — flat gray page background.
// Single card with username + password + submit.
export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const login = useAuthStore((s) => s.login)
  const isLoading = useAuthStore((s) => s.isLoading)
  const error = useAuthStore((s) => s.error)
  const user = useAuthStore((s) => s.user)
  const navigate = useNavigate()

  // Navigate to dashboard as soon as user appears in store.
  // Using useEffect (rather than calling navigate inside the async handler)
  // ensures we react to the actual committed store state, not an intermediate
  // value from a racing re-render.
  useEffect(() => {
    if (user) {
      navigate('/dashboard', { replace: true })
    }
  }, [user, navigate])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    await login({ email, password })
    // Navigation is handled by the useEffect above once user is set
  }

  return (
    <div className="min-h-screen bg-bg-app flex items-center justify-center px-4">
      <div
        className="w-full max-w-[480px] bg-bg-surface border border-border-default rounded-lg shadow-modal p-8"
      >
        {/* Logo / brand mark */}
        <div className="mb-8 text-center">
          <span className="text-xl font-semibold text-text-primary tracking-tight">
            Impl<span className="text-brand">Pilot</span>
          </span>
          <p className="mt-1 text-sm text-text-secondary">
            Project management for implementation teams
          </p>
        </div>

        <form onSubmit={(e) => { void handleSubmit(e) }} className="space-y-4">
          {/* Username */}
          <div>
            <label
              htmlFor="email"
              className="block text-xs font-semibold text-text-secondary mb-1 uppercase tracking-wide"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="
                w-full px-3 py-2 text-md text-text-primary bg-bg-surface
                border border-border-default rounded-sm
                focus:border-border-strong focus:outline-none focus:ring-2 focus:ring-brand-light
                placeholder:text-text-disabled
              "
              placeholder="you@company.com"
            />
          </div>

          {/* Password */}
          <div>
            <label
              htmlFor="password"
              className="block text-xs font-semibold text-text-secondary mb-1 uppercase tracking-wide"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="
                w-full px-3 py-2 text-md text-text-primary bg-bg-surface
                border border-border-default rounded-sm
                focus:border-border-strong focus:outline-none focus:ring-2 focus:ring-brand-light
                placeholder:text-text-disabled
              "
              placeholder="••••••••"
            />
          </div>

          {/* Error message */}
          {error && (
            <p className="text-xs text-status-red bg-status-red-bg rounded-sm px-3 py-2">
              {error}
            </p>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={isLoading}
            className="
              w-full py-2 px-4 mt-2
              bg-brand hover:bg-brand-hover
              text-text-inverse text-md font-medium
              rounded-md transition-colors
              disabled:opacity-60 disabled:cursor-not-allowed
            "
          >
            {isLoading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  )
}
