import { useEffect, useState } from 'react'
import { getSubjects, getPerformance } from '../api/client'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import Card from '../components/ui/Card'
import Spinner from '../components/ui/Spinner'

export default function History() {
  const [subjects, setSubjects] = useState([])
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [subjectFilter, setSubjectFilter] = useState('')

  useEffect(() => {
    getSubjects().then(setSubjects)
  }, [])

  useEffect(() => {
    setLoading(true)
    getPerformance(subjectFilter ? Number(subjectFilter) : undefined)
      .then(setRecords)
      .finally(() => setLoading(false))
  }, [subjectFilter])

  const total = records.length
  const correct = records.filter((r) => r.correct).length
  const accuracy = total > 0 ? Math.round((correct / total) * 100) : 0

  const byDay = {}
  records.forEach((r) => {
    const day = r.reviewed_at?.slice(0, 10) ?? 'unknown'
    if (!byDay[day]) byDay[day] = { day, correct: 0, total: 0 }
    byDay[day].total++
    if (r.correct) byDay[day].correct++
  })
  const chartData = Object.values(byDay)
    .sort((a, b) => a.day.localeCompare(b.day))
    .map((d) => ({ day: d.day, accuracy: Math.round((d.correct / d.total) * 100) }))

  return (
    <div className="max-w-4xl space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-100">Performance History</h1>
        <select
          value={subjectFilter}
          onChange={(e) => setSubjectFilter(e.target.value)}
          className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-slate-200 text-sm"
        >
          <option value="">All subjects</option>
          {subjects.map((s) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <Card>
          <p className="text-slate-400 text-sm">Reviews</p>
          <p className="text-3xl font-bold text-slate-200">{total}</p>
        </Card>
        <Card>
          <p className="text-slate-400 text-sm">Correct</p>
          <p className="text-3xl font-bold text-green-400">{correct}</p>
        </Card>
        <Card>
          <p className="text-slate-400 text-sm">Accuracy</p>
          <p className="text-3xl font-bold text-forge-400">{accuracy}%</p>
        </Card>
      </div>

      {chartData.length > 1 && (
        <Card>
          <h2 className="text-slate-300 font-semibold mb-4">Accuracy Over Time</h2>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="day" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                labelStyle={{ color: '#cbd5e1' }}
              />
              <Line type="monotone" dataKey="accuracy" stroke="#6366f1" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      )}

      <div>
        <h2 className="text-lg font-semibold text-slate-200 mb-3">Recent Reviews</h2>
        {loading && <div className="flex justify-center py-8"><Spinner /></div>}
        {!loading && records.length === 0 && (
          <p className="text-slate-500">No review history yet.</p>
        )}
        <div className="space-y-2">
          {records.slice(0, 50).map((r) => (
            <div key={r.id} className="flex items-center gap-3 px-4 py-3 bg-slate-800 rounded-lg border border-slate-700">
              <span className={`text-sm font-bold ${r.correct ? 'text-green-400' : 'text-red-400'}`}>
                {r.correct ? '✓' : '✗'}
              </span>
              <span className="flex-1 text-slate-300 text-sm">{r.ku_title}</span>
              <span className="text-slate-500 text-xs">Grade {r.grade ?? '—'}/5</span>
              <span className="text-slate-600 text-xs">{r.reviewed_at?.slice(0, 10)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
