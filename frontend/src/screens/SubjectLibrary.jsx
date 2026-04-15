import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getSubjects, createSubject, updatePlans } from '../api/client'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Spinner from '../components/ui/Spinner'
import Badge from '../components/ui/Badge'

export default function SubjectLibrary() {
  const [subjects, setSubjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', description: '', quiz_format: 'mixed', grading_strictness: 2 })
  const [creating, setCreating] = useState(false)
  const [planRunning, setPlanRunning] = useState(false)
  const [planResult, setPlanResult] = useState(null)

  const load = () =>
    getSubjects().then(setSubjects).finally(() => setLoading(false))

  useEffect(() => { load() }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!form.name.trim()) return
    setCreating(true)
    try {
      await createSubject(form)
      setForm({ name: '', description: '', quiz_format: 'mixed', grading_strictness: 2 })
      setShowForm(false)
      await load()
    } finally {
      setCreating(false)
    }
  }

  const handleUpdatePlans = async () => {
    setPlanRunning(true)
    setPlanResult(null)
    try {
      const result = await updatePlans()
      setPlanResult(result)
    } catch (e) {
      setPlanResult({ error: e.message })
    } finally {
      setPlanRunning(false)
    }
  }

  if (loading) return <div className="flex justify-center pt-20"><Spinner size="lg" /></div>

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-100">Subject Library</h1>
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={handleUpdatePlans} disabled={planRunning} title="Regenerate learning plans for all active subjects using Claude">
            {planRunning ? <><Spinner size="sm" /> Updating...</> : 'Update Plans'}
          </Button>
          <Button onClick={() => setShowForm((v) => !v)}>New Subject</Button>
        </div>
      </div>

      {planResult && (
        <div className={`p-3 rounded-lg text-sm ${planResult.error ? 'bg-red-900/40 text-red-300' : 'bg-slate-800 text-slate-300'}`}>
          {planResult.error
            ? `Error: ${planResult.error}`
            : `Updated ${planResult.updated} plan(s): ${planResult.details?.map(d => d.name).join(', ') || 'none'}`
          }
        </div>
      )}

      {showForm && (
        <Card>
          <form onSubmit={handleCreate} className="space-y-3">
            <input
              type="text"
              placeholder="Subject name"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-forge-500"
            />
            <input
              type="text"
              placeholder="Description (optional)"
              value={form.description}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-forge-500"
            />
            <div className="flex gap-3">
              <select
                value={form.quiz_format}
                onChange={(e) => setForm((f) => ({ ...f, quiz_format: e.target.value }))}
                className="bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-slate-100 text-sm"
              >
                <option value="mixed">Mixed formats</option>
                <option value="free_response">Free response</option>
                <option value="multiple_choice">Multiple choice</option>
              </select>
              <select
                value={form.grading_strictness}
                onChange={(e) => setForm((f) => ({ ...f, grading_strictness: Number(e.target.value) }))}
                className="bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-slate-100 text-sm"
              >
                <option value={1}>Lenient grading</option>
                <option value={2}>Moderate grading</option>
                <option value={3}>Strict grading</option>
              </select>
            </div>
            <div className="flex gap-2 justify-end">
              <Button variant="ghost" type="button" onClick={() => setShowForm(false)}>Cancel</Button>
              <Button type="submit" disabled={creating}>Create</Button>
            </div>
          </form>
        </Card>
      )}

      <div className="space-y-3">
        {subjects.length === 0 && (
          <p className="text-slate-500 text-center py-12">No subjects yet. Create one to get started.</p>
        )}
        {subjects.map((s) => (
          <Card key={s.id} className="flex items-center gap-4">
            <div className="flex-1">
              <p className="font-medium text-slate-200">{s.name}</p>
              {s.description && <p className="text-slate-500 text-sm">{s.description}</p>}
            </div>
            <Badge color={s.is_active ? 'green' : 'slate'}>{s.is_active ? 'Active' : 'Archived'}</Badge>
            <Link to={`/subjects/${s.id}/plan`}>
              <Button variant="ghost" size="sm">Plan →</Button>
            </Link>
          </Card>
        ))}
      </div>
    </div>
  )
}
