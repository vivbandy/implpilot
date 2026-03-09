// Dashboard placeholder — Step 8 will fill this with project cards,
// My Tasks table, and the notification bell.
export default function Dashboard() {
  return (
    <div>
      {/* Page header — Section 10.4: bg-surface, border-bottom, 56px, px-6 */}
      <header className="h-14 bg-bg-surface border-b border-border-default flex items-center px-6">
        <h1 className="text-xl font-semibold text-text-primary">Dashboard</h1>
      </header>

      {/* Page body */}
      <div className="px-6 py-6 max-w-screen-xl mx-auto">
        <p className="text-md text-text-secondary">
          Dashboard coming in Step 8 — project cards, My Tasks, and the notification bell.
        </p>
      </div>
    </div>
  )
}
