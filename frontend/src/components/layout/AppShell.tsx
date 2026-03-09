import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'

// AppShell — Section 10.4:
// Full-height flex row: Sidebar (240px fixed) + main content area (flex-1, bg-app).
// Outlet renders the current page inside the main area.
export function AppShell() {
  return (
    <div className="flex h-screen overflow-hidden bg-bg-app">
      <Sidebar />

      {/* Main content area */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
