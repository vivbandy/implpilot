import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'

// Wraps any routes that require authentication.
// Unauthenticated users are sent to /login.
// The `replace` prop prevents the login page from being added to history
// so the back button doesn't loop back to a protected page.
export function ProtectedRoute() {
  const token = useAuthStore((s) => s.token)

  if (!token) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
