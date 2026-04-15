const base = () => window.api.baseUrl

async function request(path, method = 'GET', body = undefined, isFormData = false) {
  const headers = isFormData ? {} : { 'Content-Type': 'application/json' }
  const opts = { method, headers }
  if (body !== undefined) opts.body = isFormData ? body : JSON.stringify(body)
  const res = await fetch(`${base()}${path}`, opts)
  return res.json()
}

// Subjects
export const getSubjects = () => request('/subjects', 'GET')
export const createSubject = (data) => request('/subjects', 'POST', data)
export const getSubject = (id) => request(`/subjects/${id}`, 'GET')
export const updateSubject = (id, data) => request(`/subjects/${id}`, 'PATCH', data)

// Materials
export const getMaterials = (subjectId) =>
  request(subjectId ? `/materials?subject_id=${subjectId}` : '/materials', 'GET')
export const uploadMaterial = (formData) => request('/materials', 'POST', formData, true)
export const parseNow = (id) => request(`/materials/${id}/parse`, 'POST')

// Sessions
export const startSession = (data) => request('/sessions/start', 'POST', data)
export const getNextQuestion = (sessionId) => request(`/sessions/${sessionId}/next`, 'GET')
export const submitTurn = (sessionId, data) => request(`/sessions/${sessionId}/submit`, 'POST', data)
export const endSession = (sessionId) => request(`/sessions/${sessionId}/end`, 'POST')

// Dashboard
export const getDashboard = () => request('/dashboard', 'GET')

// Performance / History
export const getPerformance = (subjectId) =>
  request(subjectId ? `/history/performance?subject_id=${subjectId}` : '/history/performance', 'GET')

// Learning Plans
export const getPlan = (subjectId) => request(`/plans/${subjectId}`, 'GET')
export const createPlan = (data) => request('/plans', 'POST', data)
