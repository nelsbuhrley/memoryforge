import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import Upload from '../screens/Upload'
import * as client from '../api/client'

vi.mock('../api/client')

function wrap(ui) { return render(<MemoryRouter>{ui}</MemoryRouter>) }

describe('Upload', () => {
  beforeEach(() => {
    client.getSubjects.mockResolvedValue([
      { id: 1, name: 'Physics', is_active: true },
    ])
    client.uploadMaterial.mockResolvedValue({ id: 5, filename: 'notes.txt', parse_status: 'pending' })
    client.getMaterials.mockResolvedValue([])
  })

  it('loads subjects into dropdown', async () => {
    wrap(<Upload />)
    await waitFor(() => expect(screen.getByText('Physics')).toBeInTheDocument())
  })

  it('upload button disabled when no file selected', async () => {
    wrap(<Upload />)
    await waitFor(() => screen.getByText('Physics'))
    expect(screen.getByRole('button', { name: /upload/i })).toBeDisabled()
  })

  it('calls uploadMaterial on submit', async () => {
    wrap(<Upload />)
    await waitFor(() => screen.getByText('Physics'))

    const file = new File(['content'], 'notes.txt', { type: 'text/plain' })
    const input = screen.getByTestId('file-input')
    fireEvent.change(input, { target: { files: [file] } })

    fireEvent.click(screen.getByRole('button', { name: /upload/i }))
    await waitFor(() => expect(client.uploadMaterial).toHaveBeenCalled())
  })
})
