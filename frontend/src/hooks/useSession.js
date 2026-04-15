import { useState } from 'react'
import { startSession, submitTurn, endSession } from '../api/client'

export function useSession() {
  const [state, setState] = useState('idle') // idle | loading | active | grading | ended | error
  const [session, setSession] = useState(null)
  const [turns, setTurns] = useState([])
  const [summary, setSummary] = useState(null)
  const [error, setError] = useState(null)

  const start = async (opts = {}) => {
    setState('loading')
    setError(null)
    try {
      const data = await startSession(opts)
      setSession(data)
      setTurns([])
      setState('active')
    } catch (e) {
      setError(e.message)
      setState('error')
    }
  }

  const submit = async (answer) => {
    if (!session) return
    setState('grading')
    try {
      const result = await submitTurn(session.session_id, answer)
      setTurns((t) => [...t, { question: session.question, answer, result }])
      setState('active')
      return result
    } catch (e) {
      setError(e.message)
      setState('active')
    }
  }

  const end = async () => {
    if (!session) return
    try {
      const data = await endSession(session.session_id)
      setSummary(data)
      setState('ended')
    } catch (e) {
      setError(e.message)
    }
  }

  return { state, session, turns, summary, error, start, submit, end }
}
