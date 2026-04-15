const colors = {
  indigo: 'bg-forge-900 text-forge-100 border-forge-700',
  green: 'bg-green-900 text-green-100 border-green-700',
  yellow: 'bg-yellow-900 text-yellow-100 border-yellow-700',
  red: 'bg-red-900 text-red-100 border-red-700',
  slate: 'bg-slate-700 text-slate-200 border-slate-600',
}

export default function Badge({ children, color = 'slate' }) {
  return (
    <span className={`inline-block px-2 py-0.5 text-xs rounded-full border font-medium ${colors[color]}`}>
      {children}
    </span>
  )
}
