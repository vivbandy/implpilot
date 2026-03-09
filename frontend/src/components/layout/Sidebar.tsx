import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  FolderKanban,
  FileText,
  Settings,
  LogOut,
  type LucideIcon,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { cn } from '@/lib/utils'

// Nav item shape — use LucideIcon directly to avoid prop type mismatch
interface NavItem {
  label: string
  to: string
  icon: LucideIcon
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard',  to: '/dashboard',  icon: LayoutDashboard },
  { label: 'Projects',   to: '/projects',   icon: FolderKanban },
  { label: 'Reports',    to: '/reports',    icon: FileText },
  { label: 'Settings',   to: '/settings',   icon: Settings },
]

// Sidebar — Section 10.4:
// 240px fixed, bg-surface, right border: border-default
// Logo top (48px), nav items, user avatar + name bottom.
// Active nav: brand-light bg, brand text, 3px left brand border.
export function Sidebar() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <aside className="w-60 shrink-0 bg-bg-surface border-r border-border-default flex flex-col h-full">
      {/* Logo — 48px height */}
      <div className="h-12 flex items-center px-5 border-b border-border-default shrink-0">
        <span className="text-lg font-semibold text-text-primary tracking-tight select-none">
          Impl<span className="text-brand">Pilot</span>
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-3 overflow-y-auto">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn(
                // Base nav item style
                'flex items-center gap-3 px-4 py-2 text-md transition-colors relative',
                isActive
                  ? // Active state — Section 10.4
                    'bg-brand-light text-brand font-semibold before:absolute before:left-0 before:top-0 before:bottom-0 before:w-[3px] before:bg-brand before:rounded-r-sm'
                  : 'text-text-secondary hover:bg-bg-subtle hover:text-text-primary'
              )
            }
          >
            <item.icon size={16} className="shrink-0" />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* User section — bottom of sidebar */}
      <div className="border-t border-border-default p-4 shrink-0">
        {user && (
          <div className="flex items-center gap-3">
            {/* Avatar — initials fallback, no image in MVP */}
            <div className="w-8 h-8 rounded-full bg-brand-light flex items-center justify-center shrink-0">
              <span className="text-xs font-semibold text-brand">
                {getInitials(user.full_name ?? user.username)}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-text-primary truncate">
                {user.full_name ?? user.username}
              </p>
              <p className="text-xs text-text-secondary capitalize">{user.role}</p>
            </div>
            <button
              onClick={handleLogout}
              title="Sign out"
              className="p-1.5 rounded-md text-text-secondary hover:bg-bg-subtle hover:text-text-primary transition-colors"
            >
              <LogOut size={15} />
            </button>
          </div>
        )}
      </div>
    </aside>
  )
}

function getInitials(name: string): string {
  return name
    .split(' ')
    .map((n) => n[0]?.toUpperCase() ?? '')
    .slice(0, 2)
    .join('')
}
