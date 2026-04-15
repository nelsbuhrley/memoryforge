import { render, screen, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import History from '../screens/History'
import * as client from '../api/client'

vi.mock('../api/client')

function wrap(ui) { return render(<MemoryRouter>{ui}</MemoryRouter>) }

const mockPerf = [
  { id: 1, session_id: 1, ku_id: 10, ku_title: "Newton's Second Law", subject_id: 1, grade: 4, correct: 1, reviewed_at: '2026-04-14T10:00:00' },
  { id: 2, session_id: 1, ku_id: 11, ku_title: 'Momentum', subject_id: 1, grade: 2, correct: 0, reviewed_at: '2026-04-14T10:05:00' },
]

describe('History', () => {
  beforeEach(() => {
    client.getSubjects.mockResolvedValue([{ id: 1, name: 'Physics' }])
    client.getPerformance.mockResolvedValue(mockPerf)
  })

  it('shows performance records', async () => {
    wrap(<History />)
    await waitFor(() => expect(screen.getByText("Newton's Second Law")).toBeInTheDocument())
  })

  it('shows correct/incorrect badges', async () => {
    wrap(<History />)
    await waitFor(() => screen.getByText("Newton's Second Law"))
    expect(screen.getByText('✓')).toBeInTheDocument()
    expect(screen.getByText('✗')).toBeInTheDocument()
  })

  it('shows accuracy summary', async () => {
    wrap(<History />)
    await waitFor(() => screen.getByText(/50%/))
  })
})
