import { NavLink } from 'react-router-dom'

const links = [
  { to: '/', label: 'Dashboard', icon: '⚡' },
  { to: '/subjects', label: 'Subjects', icon: '📚' },
  { to: '/upload', label: 'Upload', icon: '↑' },
  { to: '/session', label: 'Study', icon: '🎯' },
  { to: '/history', label: 'History', icon: '📊' },
]

export default function Nav() {
  return (
    <nav className="w-56 bg-slate-900 border-r border-slate-800 flex flex-col py-6 px-3 gap-1 shrink-0">
      <div className="px-3 mb-6">
        <h1 className="text-forge-400 font-bold text-lg tracking-tight">MemoryForge</h1>
      </div>
      {links.map(({ to, label, icon }) => (
        <NavLink
          key={to}
          to={to}
          end={to === '/'}
          className={({ isActive }) =>
            `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
              isActive
                ? 'bg-forge-900 text-forge-300'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`
          }
        >
          <span>{icon}</span>
          {label}
        </NavLink>
      ))}
    </nav>
  )
}
