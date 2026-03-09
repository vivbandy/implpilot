import axios, { type AxiosError } from 'axios'

// During development, Vite proxies /api/* to localhost:8000,
// so we use a relative base URL. In production, VITE_API_URL is set.
const BASE_URL = import.meta.env.VITE_API_URL ?? '/api/v1'

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor: attach JWT from localStorage on every request.
// The token is stored by the auth store after login.
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('implpilot_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor: on 401, clear local auth state and redirect to login.
// This catches token expiry without needing per-request error handling.
//
// IMPORTANT: skip the redirect for /auth/login itself — a 401 there means
// "wrong password", not "expired session". Redirecting would swallow the
// error before the store's catch block can set the error message.
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const isLoginRequest = error.config?.url?.includes('/auth/login')
    if (error.response?.status === 401 && !isLoginRequest) {
      localStorage.removeItem('implpilot_token')
      localStorage.removeItem('implpilot_user')
      // Hard redirect — clears all React state, forces re-auth
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// ─── Typed API helpers ────────────────────────────────────────────
// Thin wrappers so call sites don't import axios directly.

export async function apiGet<T>(path: string, params?: Record<string, unknown>): Promise<T> {
  const res = await apiClient.get<T>(path, { params })
  return res.data
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const res = await apiClient.post<T>(path, body)
  return res.data
}

export async function apiPut<T>(path: string, body?: unknown): Promise<T> {
  const res = await apiClient.put<T>(path, body)
  return res.data
}

export async function apiDelete<T = void>(path: string): Promise<T> {
  const res = await apiClient.delete<T>(path)
  return res.data
}
