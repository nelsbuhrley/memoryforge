import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  getSubjects, createSubject, getSubject, updateSubject,
  getMaterials, uploadMaterial, parseNow,
  startSession, getNextQuestion, submitTurn, endSession,
  getDashboard,
  getPerformance,
  getPlan, createPlan,
} from '../api/client'

const BASE = 'http://localhost:9147'

beforeEach(() => {
  global.fetch = vi.fn()
  window.api = { baseUrl: BASE }
})

function mockResponse(data, status = 200) {
  global.fetch.mockResolvedValueOnce({
    ok: status < 400,
    status,
    json: () => Promise.resolve(data),
  })
}

describe('subjects', () => {
  it('getSubjects calls GET /subjects', async () => {
    mockResponse([{ id: 1, name: 'Physics' }])
    const result = await getSubjects()
    expect(fetch).toHaveBeenCalledWith(`${BASE}/subjects`, expect.objectContaining({ method: 'GET' }))
    expect(result).toEqual([{ id: 1, name: 'Physics' }])
  })

  it('createSubject calls POST /subjects with body', async () => {
    mockResponse({ id: 2, name: 'Math' }, 201)
    const result = await createSubject({ name: 'Math' })
    expect(fetch).toHaveBeenCalledWith(`${BASE}/subjects`, expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({ name: 'Math' }),
    }))
    expect(result.name).toBe('Math')
  })

  it('updateSubject calls PATCH /subjects/:id', async () => {
    mockResponse({ id: 1, name: 'Updated' })
    await updateSubject(1, { name: 'Updated' })
    expect(fetch).toHaveBeenCalledWith(`${BASE}/subjects/1`, expect.objectContaining({ method: 'PATCH' }))
  })
})

describe('materials', () => {
  it('getMaterials calls GET /materials', async () => {
    mockResponse([])
    await getMaterials()
    expect(fetch).toHaveBeenCalledWith(`${BASE}/materials`, expect.objectContaining({ method: 'GET' }))
  })

  it('uploadMaterial calls POST /materials with FormData', async () => {
    mockResponse({ id: 1 }, 201)
    const fd = new FormData()
    await uploadMaterial(fd)
    expect(fetch).toHaveBeenCalledWith(`${BASE}/materials`, expect.objectContaining({ method: 'POST', body: fd }))
  })
})

describe('sessions', () => {
  it('startSession calls POST /sessions/start', async () => {
    mockResponse({ session_id: 5, queue_length: 10 }, 201)
    const result = await startSession({ subject_id: 1 })
    expect(fetch).toHaveBeenCalledWith(`${BASE}/sessions/start`, expect.objectContaining({ method: 'POST' }))
    expect(result.session_id).toBe(5)
  })

  it('endSession returns correct/total summary', async () => {
    mockResponse({ session_id: 5, correct: 8, total: 10, accuracy: 0.8 })
    const result = await endSession(5)
    expect(result.correct).toBe(8)
  })
})

describe('dashboard', () => {
  it('getDashboard calls GET /dashboard', async () => {
    mockResponse({ due_count: 5, streak: {}, streak_at_risk: false, subjects_summary: [] })
    const result = await getDashboard()
    expect(fetch).toHaveBeenCalledWith(`${BASE}/dashboard`, expect.objectContaining({ method: 'GET' }))
    expect(result.due_count).toBe(5)
  })
})
