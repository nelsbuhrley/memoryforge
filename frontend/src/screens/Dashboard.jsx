import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getDashboard } from '../api/client'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Spinner from '../components/ui/Spinner'

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="flex justify-center pt-20"><Spinner size="lg" /></div>
  if (error) return <p className="text-red-400">Failed to load dashboard: {error}</p>
  if (!data) return null

  const { due_count, streak, streak_at_risk, subjects_summary } = data

  return (
    <div className="max-w-4xl space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-100">Dashboard</h1>
        <Link to="/session">
          <Button size="lg">Start Study Session</Button>
        </Link>
      </div>

      {streak_at_risk && (
        <div className="bg-yellow-900/40 border border-yellow-700 rounded-lg p-4 text-yellow-300 text-sm">
          ⚠ Streak at risk — study today to keep your streak alive!
        </div>
      )}

      <div className="grid grid-cols-3 gap-4">
        <Card>
          <p className="text-slate-400 text-sm mb-1">Due Today</p>
          <p className="text-4xl font-bold text-forge-400">{due_count}</p>
          <p className="text-slate-500 text-xs mt-1">knowledge units</p>
        </Card>

        <Card>
          <p className="text-slate-400 text-sm mb-1">Current Streak</p>
          <p className="text-4xl font-bold text-green-400">{streak?.current_streak ?? 0}</p>
          <p className="text-slate-500 text-xs mt-1">days in a row</p>
        </Card>

        <Card>
          <p className="text-slate-400 text-sm mb-1">Longest Streak</p>
          <p className="text-4xl font-bold text-slate-300">{streak?.longest_streak ?? 0}</p>
          <p className="text-slate-500 text-xs mt-1">all-time best</p>
        </Card>
      </div>

      <div>
        <h2 className="text-lg font-semibold text-slate-200 mb-3">Subject Mastery</h2>
        <div className="space-y-3">
          {subjects_summary.length === 0 && (
            <p className="text-slate-500">No active subjects yet. <Link to="/subjects" className="text-forge-400 hover:underline">Add one →</Link></p>
          )}
          {subjects_summary.map((s) => (
            <Card key={s.id} className="flex items-center gap-4">
              <div className="flex-1">
                <p className="font-medium text-slate-200">{s.name}</p>
                <p className="text-slate-500 text-xs">{s.total_kus} knowledge units</p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-slate-200">{s.mastery_pct}%</p>
                <p className="text-slate-500 text-xs">mastered</p>
              </div>
              <div className="w-24">
                <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-forge-500 rounded-full transition-all"
                    style={{ width: `${s.mastery_pct}%` }}
                  />
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}
