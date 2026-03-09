import { create } from 'zustand'
import type { User, LoginCredentials } from '@/types'
import { apiClient } from '@/api/client'

// Token and user are persisted in localStorage so the session survives
// a page refresh. The apiClient request interceptor reads the token directly
// from localStorage — no need to keep it in Zustand state.

const TOKEN_KEY = 'implpilot_token'
const USER_KEY = 'implpilot_user'

interface AuthState {
  user: User | null
  token: string | null
  isLoading: boolean
  error: string | null

  login: (credentials: LoginCredentials) => Promise<void>
  logout: () => void
  hydrateFromStorage: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isLoading: false,
  error: null,

  // Called once on app mount to restore session from localStorage
  hydrateFromStorage: () => {
    const token = localStorage.getItem(TOKEN_KEY)
    const userRaw = localStorage.getItem(USER_KEY)
    if (token && userRaw) {
      try {
        const user = JSON.parse(userRaw) as User
        set({ token, user })
      } catch {
        // Corrupted storage — clear it
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(USER_KEY)
      }
    }
  },

  login: async (credentials) => {
    set({ isLoading: true, error: null })
    try {
      // Backend expects JSON: { email, password } — LoginRequest schema
      const tokenRes = await apiClient.post<{ access_token: string; token_type: string }>(
        '/auth/login',
        { email: credentials.email, password: credentials.password }
      )
      const token = tokenRes.data.access_token

      // Fetch the current user profile immediately after login
      const userRes = await apiClient.get<User>('/auth/me', {
        headers: { Authorization: `Bearer ${token}` },
      })
      const user = userRes.data

      localStorage.setItem(TOKEN_KEY, token)
      localStorage.setItem(USER_KEY, JSON.stringify(user))

      set({ token, user, isLoading: false })
    } catch (err: unknown) {
      // FastAPI returns detail as a string for auth errors (401)
      // but as an array of {loc, msg, type} objects for validation errors (422).
      // We must handle both to avoid passing a non-string into {error} in JSX.
      const raw = (err as { response?: { data?: { detail?: unknown } } })
        ?.response?.data?.detail
      let detail: string
      if (typeof raw === 'string') {
        detail = raw
      } else if (Array.isArray(raw) && raw.length > 0) {
        detail = (raw[0] as { msg?: string })?.msg ?? 'Login failed. Check your credentials.'
      } else {
        detail = 'Login failed. Check your credentials.'
      }
      set({ isLoading: false, error: detail })
    }
  },

  logout: () => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    set({ user: null, token: null, error: null })
  },
}))
