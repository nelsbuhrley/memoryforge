import { render, screen, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import Dashboard from '../screens/Dashboard'
import * as client from '../api/client'

vi.mock('../api/client')

const mockDashboard = {
  due_count: 12,
  streak: { current_streak: 5, longest_streak: 14 },
  streak_at_risk: false,
  subjects_summary: [
    { id: 1, name: 'Physics', total_kus: 40, mastered_kus: 20, mastery_pct: 50.0 },
  ],
}

function wrap(ui) {
  return render(<MemoryRouter>{ui}</MemoryRouter>)
}

describe('Dashboard', () => {
  beforeEach(() => {
    client.getDashboard.mockResolvedValue(mockDashboard)
  })

  it('shows due count after load', async () => {
    wrap(<Dashboard />)
    await waitFor(() => expect(screen.getByText('12')).toBeInTheDocument())
  })

  it('shows streak count', async () => {
    wrap(<Dashboard />)
    await waitFor(() => expect(screen.getByText('5')).toBeInTheDocument())
  })

  it('shows subject mastery percentage', async () => {
    wrap(<Dashboard />)
    await waitFor(() => expect(screen.getByText('Physics')).toBeInTheDocument())
    expect(screen.getByText('50%')).toBeInTheDocument()
  })

  it('shows streak at risk warning when at_risk is true', async () => {
    client.getDashboard.mockResolvedValueOnce({ ...mockDashboard, streak_at_risk: true })
    wrap(<Dashboard />)
    await waitFor(() => expect(screen.getByText(/streak at risk/i)).toBeInTheDocument())
  })
})
