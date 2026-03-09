import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useAuthStore } from '@/store/authStore'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { AppShell } from '@/components/layout/AppShell'
import Login from '@/pages/Login'
import Dashboard from '@/pages/Dashboard'

export default function App() {
  const hydrateFromStorage = useAuthStore((s) => s.hydrateFromStorage)

  // Restore session from localStorage on first mount.
  // This runs before any route renders, so ProtectedRoute sees the token.
  useEffect(() => {
    hydrateFromStorage()
  }, [hydrateFromStorage])

  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<Login />} />

        {/* Protected routes — all wrapped in AppShell */}
        <Route element={<ProtectedRoute />}>
          <Route element={<AppShell />}>
            <Route path="/dashboard" element={<Dashboard />} />
            {/* Step 8 will add: /projects, /projects/:id, /tasks/:id */}
            {/* Step 10 will add: /reports */}
            {/* Step 12 will add: /settings */}
          </Route>
        </Route>

        {/* Default redirect */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
