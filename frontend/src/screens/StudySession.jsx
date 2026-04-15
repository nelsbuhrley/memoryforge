import { useEffect, useState } from 'react'
import { getSubjects } from '../api/client'
import { useSession } from '../hooks/useSession'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Spinner from '../components/ui/Spinner'
import Badge from '../components/ui/Badge'

export default function StudySession() {
  const [subjects, setSubjects] = useState([])
  const [selectedSubject, setSelectedSubject] = useState('')
  const [answer, setAnswer] = useState('')
  const [lastResult, setLastResult] = useState(null)
  const { state, session, turns, summary, error, start, submit, end } = useSession()

  useEffect(() => {
    getSubjects().then((s) => {
      setSubjects(s)
      if (s.length) setSelectedSubject(String(s[0].id))
    })
  }, [])

  const handleStart = () => {
    start({ subject_id: selectedSubject ? Number(selectedSubject) : undefined })
  }

  const handleSubmit = async () => {
    if (!answer.trim()) return
    const result = await submit(answer)
    setLastResult(result)
    setAnswer('')
  }

  if (state === 'ended' && summary) {
    const pct = Math.round(summary.accuracy * 100)
    return (
      <div className="max-w-xl mx-auto text-center space-y-6 pt-16">
        <h1 className="text-3xl font-bold text-slate-100">Session Complete!</h1>
        <Card>
          <p className="text-7xl font-bold text-forge-400">{pct}%</p>
          <p className="text-slate-400 mt-2">{summary.correct} correct out of {summary.total}</p>
        </Card>
        <Button onClick={() => { setLastResult(null); start({ subject_id: selectedSubject ? Number(selectedSubject) : undefined }) }}>
          Start Another
        </Button>
      </div>
    )
  }

  if (state === 'idle' || state === 'error') {
    return (
      <div className="max-w-md mx-auto space-y-6 pt-16">
        <h1 className="text-2xl font-bold text-slate-100 text-center">Study Session</h1>
        {error && <p className="text-red-400 text-sm text-center">{error}</p>}
        <Card className="space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">Subject (optional)</label>
            <select
              value={selectedSubject}
              onChange={(e) => setSelectedSubject(e.target.value)}
              className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-slate-100 text-sm"
            >
              <option value="">All subjects</option>
              {subjects.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </div>
          <Button className="w-full" onClick={handleStart}>Start Session</Button>
        </Card>
      </div>
    )
  }

  if (state === 'loading') {
    return <div className="flex justify-center pt-20"><Spinner size="lg" /></div>
  }

  const ku = session?.current_ku
  const question = session?.question

  // Guard: session active but question not yet loaded
  if (state === 'active' && !question) {
    return <div className="flex justify-center pt-20"><Spinner size="lg" /></div>
  }

  return (
    <div className="max-w-2xl space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-slate-100">Study Session</h1>
        <div className="flex items-center gap-3">
          <span className="text-slate-500 text-sm">{turns.length} answered</span>
          <Button variant="ghost" size="sm" onClick={end}>End Session</Button>
        </div>
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      {ku && (
        <Card>
          <Badge color="indigo">{ku.concept}</Badge>
          <p className="text-slate-400 text-xs mt-1">{ku.concept_summary}</p>
        </Card>
      )}

      <Card>
        <p className="text-slate-200 text-lg leading-relaxed">{question}</p>
      </Card>

      {lastResult && (
        <Card className={`border-l-4 ${lastResult.correct ? 'border-l-green-500' : 'border-l-red-500'}`}>
          <div className="flex items-center gap-2 mb-2">
            <Badge color={lastResult.correct ? 'green' : 'red'}>
              {lastResult.correct ? '✓ Correct' : '✗ Incorrect'}
            </Badge>
            <span className="text-slate-500 text-xs">Grade {lastResult.grade}/5</span>
          </div>
          <p className="text-slate-300 text-sm">{lastResult.feedback}</p>
          {lastResult.reteach && (
            <div className="mt-3 pt-3 border-t border-slate-700">
              <p className="text-slate-400 text-xs mb-1">Reteach:</p>
              <p className="text-slate-300 text-sm">{lastResult.reteach}</p>
            </div>
          )}
        </Card>
      )}

      {lastResult ? (
        <div className="flex justify-end">
          <Button onClick={() => setLastResult(null)} size="lg">
            Next Question →
          </Button>
        </div>
      ) : (
        <Card>
          <textarea
            placeholder="Your answer..."
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && e.metaKey) handleSubmit() }}
            rows={4}
            spellCheck={true}
            autoCorrect="on"
            autoCapitalize="sentences"
            className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-slate-100 text-sm resize-none focus:outline-none focus:border-forge-500"
          />
          <div className="flex justify-end mt-2">
            <Button
              onClick={handleSubmit}
              disabled={!answer.trim() || state === 'grading'}
            >
              {state === 'grading' ? <><Spinner size="sm" /> Grading...</> : 'Submit'}
            </Button>
          </div>
        </Card>
      )}
    </div>
  )
}
