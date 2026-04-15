import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import SubjectLibrary from '../screens/SubjectLibrary'
import * as client from '../api/client'

vi.mock('../api/client')

function wrap(ui) { return render(<MemoryRouter>{ui}</MemoryRouter>) }

describe('SubjectLibrary', () => {
  beforeEach(() => {
    client.getSubjects.mockResolvedValue([
      { id: 1, name: 'Physics', description: 'Mechanics', is_active: true, quiz_format: 'mixed' },
    ])
    client.createSubject.mockResolvedValue({ id: 2, name: 'Math', description: '', is_active: true, quiz_format: 'mixed' })
    client.getMaterials.mockResolvedValue([])
  })

  it('lists existing subjects', async () => {
    wrap(<SubjectLibrary />)
    await waitFor(() => expect(screen.getByText('Physics')).toBeInTheDocument())
  })

  it('shows create subject form', async () => {
    wrap(<SubjectLibrary />)
    await waitFor(() => screen.getByText('Physics'))
    fireEvent.click(screen.getByRole('button', { name: /new subject/i }))
    expect(screen.getByPlaceholderText(/subject name/i)).toBeInTheDocument()
  })

  it('creates a subject and refreshes list', async () => {
    client.getSubjects
      .mockResolvedValueOnce([{ id: 1, name: 'Physics', description: '', is_active: true, quiz_format: 'mixed' }])
      .mockResolvedValueOnce([
        { id: 1, name: 'Physics', description: '', is_active: true, quiz_format: 'mixed' },
        { id: 2, name: 'Math', description: '', is_active: true, quiz_format: 'mixed' },
      ])
    wrap(<SubjectLibrary />)
    await waitFor(() => screen.getByText('Physics'))
    fireEvent.click(screen.getByRole('button', { name: /new subject/i }))
    await userEvent.type(screen.getByPlaceholderText(/subject name/i), 'Math')
    fireEvent.click(screen.getByRole('button', { name: /^create$/i }))
    await waitFor(() => expect(client.createSubject).toHaveBeenCalledWith(expect.objectContaining({ name: 'Math' })))
  })
})
