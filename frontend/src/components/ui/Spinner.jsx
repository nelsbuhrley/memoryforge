export default function Spinner({ size = 'md' }) {
  const s = size === 'sm' ? 'w-4 h-4' : size === 'lg' ? 'w-8 h-8' : 'w-6 h-6'
  return (
    <div className={`${s} animate-spin rounded-full border-2 border-slate-600 border-t-forge-500`} />
  )
}
