import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import StudySession from '../screens/StudySession'
import * as client from '../api/client'

vi.mock('../api/client')

function wrap(ui) { return render(<MemoryRouter>{ui}</MemoryRouter>) }

const mockStart = {
  session_id: 1,
  queue_length: 5,
  current_ku: { id: 10, concept: 'Newton\'s Second Law', concept_summary: 'F=ma' },
  question: 'Explain Newton\'s Second Law in your own words.',
}

const mockTurn = {
  correct: true,
  grade: 4,
  feedback: 'Great answer! F=ma is well stated.',
  reteach: null,
}

const mockEnd = { session_id: 1, correct: 4, total: 5, accuracy: 0.8 }

describe('StudySession', () => {
  beforeEach(() => {
    client.getSubjects.mockResolvedValue([{ id: 1, name: 'Physics' }])
    client.startSession.mockResolvedValue(mockStart)
    client.submitTurn.mockResolvedValue(mockTurn)
    client.endSession.mockResolvedValue(mockEnd)
  })

  it('shows start screen initially', async () => {
    wrap(<StudySession />)
    await waitFor(() => expect(screen.getByRole('button', { name: /start session/i })).toBeInTheDocument())
  })

  it('shows question after starting session', async () => {
    wrap(<StudySession />)
    await waitFor(() => screen.getByRole('button', { name: /start session/i }))
    fireEvent.click(screen.getByRole('button', { name: /start session/i }))
    await waitFor(() => expect(screen.getAllByText(/newton/i).length).toBeGreaterThan(0))
  })

  it('submits answer and shows feedback', async () => {
    wrap(<StudySession />)
    await waitFor(() => screen.getByRole('button', { name: /start session/i }))
    fireEvent.click(screen.getByRole('button', { name: /start session/i }))
    await waitFor(() => screen.getAllByText(/newton/i))

    const textarea = screen.getByPlaceholderText(/your answer/i)
    await userEvent.type(textarea, 'Force equals mass times acceleration')
    fireEvent.click(screen.getByRole('button', { name: /submit/i }))

    await waitFor(() => expect(screen.getByText(/great answer/i)).toBeInTheDocument())
  })

  it('shows session summary after end', async () => {
    wrap(<StudySession />)
    await waitFor(() => screen.getByRole('button', { name: /start session/i }))
    fireEvent.click(screen.getByRole('button', { name: /start session/i }))
    await waitFor(() => screen.getAllByText(/newton/i))

    const textarea = screen.getByPlaceholderText(/your answer/i)
    await userEvent.type(textarea, 'F = ma')
    fireEvent.click(screen.getByRole('button', { name: /submit/i }))
    await waitFor(() => screen.getByText(/great answer/i))

    fireEvent.click(screen.getByRole('button', { name: /end session/i }))
    await waitFor(() => expect(screen.getByText(/session complete/i)).toBeInTheDocument())
    expect(screen.getByText('80%')).toBeInTheDocument()
  })
})
