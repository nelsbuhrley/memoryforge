# MemoryForge Plan 2: Electron + React Frontend

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Electron + React 19 desktop frontend for MemoryForge with 6 screens (Dashboard, Subject Library, Upload, Study Session, Learning Plan, Performance History) communicating with the Plan 1 FastAPI backend.

**Architecture:** Electron shell spawns the FastAPI uvicorn server as a subprocess, then opens a browser window pointed at a Vite-built React app. All API calls go to `http://localhost:9147`. Context isolation is enforced via a preload script that only exposes the API base URL — no Node.js APIs leak to the renderer.

**Tech Stack:** Electron 34, React 19, React Router 7, TailwindCSS 3, Recharts 2, Vite 6, Vitest 2, @testing-library/react 16

---

## File Map

```
frontend/
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── index.html
├── electron/
│   ├── main.js          ← main process: BrowserWindow + uvicorn lifecycle
│   ├── preload.js       ← contextBridge: window.api.baseUrl
│   └── server.js        ← FastAPI process start/stop
├── src/
│   ├── main.jsx         ← ReactDOM.createRoot
│   ├── App.jsx          ← BrowserRouter + routes + Layout
│   ├── api/
│   │   └── client.js    ← fetch wrappers for all route groups
│   ├── components/
│   │   ├── Layout.jsx   ← sidebar nav + main content area
│   │   ├── Nav.jsx      ← navigation links
│   │   └── ui/
│   │       ├── Button.jsx
│   │       ├── Card.jsx
│   │       ├── Badge.jsx
│   │       └── Spinner.jsx
│   ├── screens/
│   │   ├── Dashboard.jsx
│   │   ├── SubjectLibrary.jsx
│   │   ├── Upload.jsx
│   │   ├── StudySession.jsx
│   │   ├── LearningPlan.jsx
│   │   └── History.jsx
│   └── hooks/
│       └── useSession.js
└── src/test/
    ├── setup.js
    ├── client.test.js
    ├── Dashboard.test.jsx
    ├── SubjectLibrary.test.jsx
    ├── Upload.test.jsx
    ├── StudySession.test.jsx
    └── History.test.jsx
```

---

## Task 1: Project Scaffolding

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.jsx`
- Create: `frontend/src/App.jsx`
- Create: `frontend/src/test/setup.js`
- Create: `frontend/electron/main.js`
- Create: `frontend/electron/preload.js`
- Create: `frontend/electron/server.js`

- [ ] **Step 1: Create `frontend/package.json`**

```json
{
  "name": "memoryforge",
  "version": "0.1.0",
  "private": true,
  "main": "electron/main.js",
  "scripts": {
    "dev": "concurrently \"vite --port 5173\" \"wait-on http://localhost:5173 && electron .\"",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-router-dom": "^7.0.0",
    "recharts": "^2.12.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.6.0",
    "@testing-library/react": "^16.3.0",
    "@testing-library/user-event": "^14.6.0",
    "@vitejs/plugin-react": "^4.3.0",
    "autoprefixer": "^10.4.0",
    "concurrently": "^9.0.0",
    "electron": "^34.0.0",
    "electron-builder": "^25.0.0",
    "jsdom": "^25.0.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "vite": "^6.0.0",
    "vitest": "^2.2.0",
    "wait-on": "^8.0.0"
  }
}
```

- [ ] **Step 2: Create `frontend/vite.config.js`**

```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: './',
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.js',
    globals: true,
  },
})
```

- [ ] **Step 3: Create `frontend/tailwind.config.js`**

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        forge: {
          50: '#f0f4ff',
          100: '#e0e9ff',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          900: '#1e1b4b',
        },
      },
    },
  },
  plugins: [],
}
```

- [ ] **Step 4: Create `frontend/postcss.config.js`**

```js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 5: Create `frontend/index.html`**

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>MemoryForge</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

- [ ] **Step 6: Create `frontend/src/main.jsx`**

```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
```

- [ ] **Step 7: Create `frontend/src/index.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 8: Create placeholder `frontend/src/App.jsx`** (full version in Task 3)

```jsx
export default function App() {
  return <div className="p-4 text-forge-500">MemoryForge loading...</div>
}
```

- [ ] **Step 9: Create `frontend/src/test/setup.js`**

```js
import '@testing-library/jest-dom'
```

- [ ] **Step 10: Create `frontend/electron/server.js`**

```js
const { spawn } = require('child_process')
const path = require('path')

const REPO_ROOT = path.join(__dirname, '..', '..')
const VENV_PYTHON = path.join(REPO_ROOT, 'backend', '.venv', 'bin', 'python')
const BACKEND_DIR = path.join(REPO_ROOT, 'backend')

let serverProcess = null

function startServer() {
  return new Promise((resolve, reject) => {
    serverProcess = spawn(
      VENV_PYTHON,
      ['-m', 'uvicorn', 'memoryforge.api.app:create_app', '--factory',
       '--host', '127.0.0.1', '--port', '9147'],
      {
        cwd: BACKEND_DIR,
        env: { ...process.env, PYTHONPATH: BACKEND_DIR },
      }
    )

    serverProcess.stdout.on('data', (data) => {
      const msg = data.toString()
      if (msg.includes('Application startup complete')) {
        resolve()
      }
    })

    serverProcess.stderr.on('data', (data) => {
      const msg = data.toString()
      // uvicorn logs startup to stderr
      if (msg.includes('Application startup complete')) {
        resolve()
      }
    })

    serverProcess.on('error', reject)

    // Fallback: resolve after 3s if startup log not detected
    setTimeout(resolve, 3000)
  })
}

function stopServer() {
  if (serverProcess) {
    serverProcess.kill()
    serverProcess = null
  }
}

module.exports = { startServer, stopServer }
```

- [ ] **Step 11: Create `frontend/electron/preload.js`**

```js
const { contextBridge } = require('electron')

contextBridge.exposeInMainWorld('api', {
  baseUrl: 'http://localhost:9147',
})
```

- [ ] **Step 12: Create `frontend/electron/main.js`**

```js
const { app, BrowserWindow } = require('electron')
const path = require('path')
const { startServer, stopServer } = require('./server')

const isDev = process.env.NODE_ENV !== 'production'

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    titleBarStyle: 'hiddenInset',
    backgroundColor: '#0f172a',
  })

  if (isDev) {
    win.loadURL('http://localhost:5173')
    win.webContents.openDevTools()
  } else {
    win.loadFile(path.join(__dirname, '..', 'dist', 'index.html'))
  }
}

app.whenReady().then(async () => {
  if (!isDev) {
    await startServer()
  }
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  stopServer()
  if (process.platform !== 'darwin') app.quit()
})

app.on('will-quit', () => {
  stopServer()
})
```

- [ ] **Step 13: Install dependencies**

```bash
cd frontend && npm install
```

Expected: `node_modules/` created, no errors.

- [ ] **Step 14: Verify Vite starts**

```bash
cd frontend && npm run build
```

Expected: `dist/` created with `index.html`. No errors.

- [ ] **Step 15: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold Electron + React + Vite + Tailwind frontend"
```

---

## Task 2: API Client

**Files:**
- Create: `frontend/src/api/client.js`
- Create: `frontend/src/test/client.test.js`

- [ ] **Step 1: Write failing tests**

Create `frontend/src/test/client.test.js`:

```js
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd frontend && npx vitest run src/test/client.test.js
```

Expected: FAIL — "Cannot find module '../api/client'"

- [ ] **Step 3: Implement `frontend/src/api/client.js`**

```js
const base = () => (window.api?.baseUrl ?? 'http://localhost:9147')

async function req(method, path, body, isFormData = false) {
  const headers = isFormData ? {} : { 'Content-Type': 'application/json' }
  const res = await fetch(`${base()}${path}`, {
    method,
    headers,
    body: body ? (isFormData ? body : JSON.stringify(body)) : undefined,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw Object.assign(new Error(err.detail ?? 'Request failed'), { status: res.status })
  }
  return res.json()
}

// Subjects
export const getSubjects = (activeOnly = false) =>
  req('GET', `/subjects${activeOnly ? '?active_only=true' : ''}`)
export const createSubject = (body) => req('POST', '/subjects', body)
export const getSubject = (id) => req('GET', `/subjects/${id}`)
export const updateSubject = (id, body) => req('PATCH', `/subjects/${id}`, body)

// Materials
export const getMaterials = (subjectId) =>
  req('GET', `/materials${subjectId ? `?subject_id=${subjectId}` : ''}`)
export const uploadMaterial = (formData) => req('POST', '/materials', formData, true)
export const parseNow = (id) => req('POST', `/materials/${id}/parse-now`)

// Sessions
export const startSession = (body) => req('POST', '/sessions/start', body)
export const getNextQuestion = (sessionId) => req('GET', `/sessions/${sessionId}/next`)
export const submitTurn = (sessionId, answer) =>
  req('POST', `/sessions/${sessionId}/turn`, { answer })
export const endSession = (sessionId) => req('POST', `/sessions/${sessionId}/end`)

// Dashboard
export const getDashboard = () => req('GET', '/dashboard')

// Plans
export const getPlan = (subjectId) => req('GET', `/plans/${subjectId}`)
export const createPlan = (body) => req('POST', '/plans', body)

// History
export const getPerformance = (subjectId, limit = 100) =>
  req('GET', `/history/performance${subjectId ? `?subject_id=${subjectId}&limit=${limit}` : `?limit=${limit}`}`)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd frontend && npx vitest run src/test/client.test.js
```

Expected: 9 tests pass.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api/ frontend/src/test/client.test.js
git commit -m "feat: API client with typed fetch wrappers for all route groups"
```

---

## Task 3: Layout Shell + UI Components

**Files:**
- Create: `frontend/src/components/Layout.jsx`
- Create: `frontend/src/components/Nav.jsx`
- Create: `frontend/src/components/ui/Button.jsx`
- Create: `frontend/src/components/ui/Card.jsx`
- Create: `frontend/src/components/ui/Badge.jsx`
- Create: `frontend/src/components/ui/Spinner.jsx`
- Modify: `frontend/src/App.jsx`

- [ ] **Step 1: Create `frontend/src/components/ui/Button.jsx`**

```jsx
const variants = {
  primary: 'bg-forge-600 hover:bg-forge-700 text-white',
  secondary: 'bg-slate-700 hover:bg-slate-600 text-white',
  ghost: 'bg-transparent hover:bg-slate-800 text-slate-300',
  danger: 'bg-red-600 hover:bg-red-700 text-white',
}

const sizes = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
}

export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  onClick,
  type = 'button',
  className = '',
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`
        inline-flex items-center justify-center gap-2 rounded-lg font-medium
        transition-colors focus:outline-none focus:ring-2 focus:ring-forge-500 focus:ring-offset-2
        focus:ring-offset-slate-900 disabled:opacity-50 disabled:cursor-not-allowed
        ${variants[variant]} ${sizes[size]} ${className}
      `}
    >
      {children}
    </button>
  )
}
```

- [ ] **Step 2: Create `frontend/src/components/ui/Card.jsx`**

```jsx
export default function Card({ children, className = '' }) {
  return (
    <div className={`bg-slate-800 border border-slate-700 rounded-xl p-5 ${className}`}>
      {children}
    </div>
  )
}
```

- [ ] **Step 3: Create `frontend/src/components/ui/Badge.jsx`**

```jsx
const colors = {
  indigo: 'bg-forge-900 text-forge-100 border-forge-700',
  green: 'bg-green-900 text-green-100 border-green-700',
  yellow: 'bg-yellow-900 text-yellow-100 border-yellow-700',
  red: 'bg-red-900 text-red-100 border-red-700',
  slate: 'bg-slate-700 text-slate-200 border-slate-600',
}

export default function Badge({ children, color = 'slate' }) {
  return (
    <span className={`inline-block px-2 py-0.5 text-xs rounded-full border font-medium ${colors[color]}`}>
      {children}
    </span>
  )
}
```

- [ ] **Step 4: Create `frontend/src/components/ui/Spinner.jsx`**

```jsx
export default function Spinner({ size = 'md' }) {
  const s = size === 'sm' ? 'w-4 h-4' : size === 'lg' ? 'w-8 h-8' : 'w-6 h-6'
  return (
    <div className={`${s} animate-spin rounded-full border-2 border-slate-600 border-t-forge-500`} />
  )
}
```

- [ ] **Step 5: Create `frontend/src/components/Nav.jsx`**

```jsx
import { NavLink } from 'react-router-dom'

const links = [
  { to: '/', label: 'Dashboard', icon: '⚡' },
  { to: '/subjects', label: 'Subjects', icon: '📚' },
  { to: '/upload', label: 'Upload', icon: '↑' },
  { to: '/session', label: 'Study', icon: '🎯' },
  { to: '/history', label: 'History', icon: '📊' },
]

export default function Nav() {
  return (
    <nav className="w-56 bg-slate-900 border-r border-slate-800 flex flex-col py-6 px-3 gap-1 shrink-0">
      <div className="px-3 mb-6">
        <h1 className="text-forge-400 font-bold text-lg tracking-tight">MemoryForge</h1>
      </div>
      {links.map(({ to, label, icon }) => (
        <NavLink
          key={to}
          to={to}
          end={to === '/'}
          className={({ isActive }) =>
            `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
              isActive
                ? 'bg-forge-900 text-forge-300'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`
          }
        >
          <span>{icon}</span>
          {label}
        </NavLink>
      ))}
    </nav>
  )
}
```

- [ ] **Step 6: Create `frontend/src/components/Layout.jsx`**

```jsx
import { Outlet } from 'react-router-dom'
import Nav from './Nav'

export default function Layout() {
  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden">
      <Nav />
      <main className="flex-1 overflow-y-auto p-8">
        <Outlet />
      </main>
    </div>
  )
}
```

- [ ] **Step 7: Rewrite `frontend/src/App.jsx` with full router**

```jsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './screens/Dashboard'
import SubjectLibrary from './screens/SubjectLibrary'
import Upload from './screens/Upload'
import StudySession from './screens/StudySession'
import LearningPlan from './screens/LearningPlan'
import History from './screens/History'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="subjects" element={<SubjectLibrary />} />
          <Route path="subjects/:id/plan" element={<LearningPlan />} />
          <Route path="upload" element={<Upload />} />
          <Route path="session" element={<StudySession />} />
          <Route path="history" element={<History />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
```

- [ ] **Step 8: Create placeholder screens** (prevents import errors; real implementations in Tasks 4–8)

Create each as a minimal stub:

`frontend/src/screens/Dashboard.jsx`:
```jsx
export default function Dashboard() { return <div>Dashboard</div> }
```

`frontend/src/screens/SubjectLibrary.jsx`:
```jsx
export default function SubjectLibrary() { return <div>Subjects</div> }
```

`frontend/src/screens/Upload.jsx`:
```jsx
export default function Upload() { return <div>Upload</div> }
```

`frontend/src/screens/StudySession.jsx`:
```jsx
export default function StudySession() { return <div>Study</div> }
```

`frontend/src/screens/LearningPlan.jsx`:
```jsx
export default function LearningPlan() { return <div>Plan</div> }
```

`frontend/src/screens/History.jsx`:
```jsx
export default function History() { return <div>History</div> }
```

- [ ] **Step 9: Verify build**

```bash
cd frontend && npm run build
```

Expected: `dist/` rebuilt without errors.

- [ ] **Step 10: Commit**

```bash
git add frontend/src/
git commit -m "feat: layout shell, nav, and UI component primitives"
```

---

## Task 4: Dashboard Screen

**Files:**
- Modify: `frontend/src/screens/Dashboard.jsx`
- Create: `frontend/src/test/Dashboard.test.jsx`

- [ ] **Step 1: Write failing tests**

Create `frontend/src/test/Dashboard.test.jsx`:

```jsx
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
    expect(screen.getByText('50.0%')).toBeInTheDocument()
  })

  it('shows streak at risk warning when at_risk is true', async () => {
    client.getDashboard.mockResolvedValueOnce({ ...mockDashboard, streak_at_risk: true })
    wrap(<Dashboard />)
    await waitFor(() => expect(screen.getByText(/streak at risk/i)).toBeInTheDocument())
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd frontend && npx vitest run src/test/Dashboard.test.jsx
```

Expected: FAIL — stub Dashboard doesn't fetch data.

- [ ] **Step 3: Implement `frontend/src/screens/Dashboard.jsx`**

```jsx
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getDashboard } from '../api/client'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Spinner from '../components/ui/Spinner'
import Badge from '../components/ui/Badge'

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="flex justify-center pt-20"><Spinner size="lg" /></div>
  if (error) return <p className="text-red-400">Failed to load dashboard: {error}</p>
  if (!data) return null

  const { due_count, streak, streak_at_risk, subjects_summary } = data

  return (
    <div className="max-w-4xl space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-100">Dashboard</h1>
        <Link to="/session">
          <Button size="lg">Start Study Session</Button>
        </Link>
      </div>

      {streak_at_risk && (
        <div className="bg-yellow-900/40 border border-yellow-700 rounded-lg p-4 text-yellow-300 text-sm">
          ⚠ Streak at risk — study today to keep your streak alive!
        </div>
      )}

      <div className="grid grid-cols-3 gap-4">
        <Card>
          <p className="text-slate-400 text-sm mb-1">Due Today</p>
          <p className="text-4xl font-bold text-forge-400">{due_count}</p>
          <p className="text-slate-500 text-xs mt-1">knowledge units</p>
        </Card>

        <Card>
          <p className="text-slate-400 text-sm mb-1">Current Streak</p>
          <p className="text-4xl font-bold text-green-400">{streak?.current_streak ?? 0}</p>
          <p className="text-slate-500 text-xs mt-1">days in a row</p>
        </Card>

        <Card>
          <p className="text-slate-400 text-sm mb-1">Longest Streak</p>
          <p className="text-4xl font-bold text-slate-300">{streak?.longest_streak ?? 0}</p>
          <p className="text-slate-500 text-xs mt-1">all-time best</p>
        </Card>
      </div>

      <div>
        <h2 className="text-lg font-semibold text-slate-200 mb-3">Subject Mastery</h2>
        <div className="space-y-3">
          {subjects_summary.length === 0 && (
            <p className="text-slate-500">No active subjects yet. <Link to="/subjects" className="text-forge-400 hover:underline">Add one →</Link></p>
          )}
          {subjects_summary.map((s) => (
            <Card key={s.id} className="flex items-center gap-4">
              <div className="flex-1">
                <p className="font-medium text-slate-200">{s.name}</p>
                <p className="text-slate-500 text-xs">{s.total_kus} knowledge units</p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-slate-200">{s.mastery_pct}%</p>
                <p className="text-slate-500 text-xs">mastered</p>
              </div>
              <div className="w-24">
                <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-forge-500 rounded-full transition-all"
                    style={{ width: `${s.mastery_pct}%` }}
                  />
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd frontend && npx vitest run src/test/Dashboard.test.jsx
```

Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/screens/Dashboard.jsx frontend/src/test/Dashboard.test.jsx
git commit -m "feat: Dashboard screen with due count, streak, subject mastery"
```

---

## Task 5: Subject Library Screen

**Files:**
- Modify: `frontend/src/screens/SubjectLibrary.jsx`
- Create: `frontend/src/test/SubjectLibrary.test.jsx`

- [ ] **Step 1: Write failing tests**

Create `frontend/src/test/SubjectLibrary.test.jsx`:

```jsx
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd frontend && npx vitest run src/test/SubjectLibrary.test.jsx
```

Expected: FAIL.

- [ ] **Step 3: Implement `frontend/src/screens/SubjectLibrary.jsx`**

```jsx
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getSubjects, createSubject, getMaterials } from '../api/client'
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

  if (loading) return <div className="flex justify-center pt-20"><Spinner size="lg" /></div>

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-100">Subject Library</h1>
        <Button onClick={() => setShowForm((v) => !v)}>New Subject</Button>
      </div>

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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd frontend && npx vitest run src/test/SubjectLibrary.test.jsx
```

Expected: 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/screens/SubjectLibrary.jsx frontend/src/test/SubjectLibrary.test.jsx
git commit -m "feat: Subject Library screen with create form"
```

---

## Task 6: Upload Material Screen

**Files:**
- Modify: `frontend/src/screens/Upload.jsx`
- Create: `frontend/src/test/Upload.test.jsx`

- [ ] **Step 1: Write failing tests**

Create `frontend/src/test/Upload.test.jsx`:

```jsx
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd frontend && npx vitest run src/test/Upload.test.jsx
```

Expected: FAIL.

- [ ] **Step 3: Implement `frontend/src/screens/Upload.jsx`**

```jsx
import { useEffect, useState } from 'react'
import { getSubjects, uploadMaterial, getMaterials, parseNow } from '../api/client'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Spinner from '../components/ui/Spinner'
import Badge from '../components/ui/Badge'

const STATUS_COLOR = {
  pending: 'slate',
  processing: 'yellow',
  complete: 'green',
  error: 'red',
}

export default function Upload() {
  const [subjects, setSubjects] = useState([])
  const [materials, setMaterials] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedSubject, setSelectedSubject] = useState('')
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState(null)

  const load = async () => {
    const [s, m] = await Promise.all([getSubjects(), getMaterials()])
    setSubjects(s)
    setMaterials(m)
    if (s.length && !selectedSubject) setSelectedSubject(String(s[0].id))
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const handleUpload = async () => {
    if (!file || !selectedSubject) return
    setUploading(true)
    setUploadError(null)
    try {
      const fd = new FormData()
      fd.append('subject_id', selectedSubject)
      fd.append('file', file)
      await uploadMaterial(fd)
      setFile(null)
      await load()
    } catch (e) {
      setUploadError(e.message)
    } finally {
      setUploading(false)
    }
  }

  const handleParseNow = async (id) => {
    await parseNow(id).catch(() => null)
    await load()
  }

  if (loading) return <div className="flex justify-center pt-20"><Spinner size="lg" /></div>

  return (
    <div className="max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold text-slate-100">Upload Material</h1>

      <Card className="space-y-4">
        <div>
          <label className="block text-sm text-slate-400 mb-1">Subject</label>
          <select
            value={selectedSubject}
            onChange={(e) => setSelectedSubject(e.target.value)}
            className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-slate-100 text-sm"
          >
            {subjects.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm text-slate-400 mb-1">File</label>
          <input
            data-testid="file-input"
            type="file"
            accept=".pdf,.txt,.md,.docx"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="block w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-forge-900 file:text-forge-300 file:text-sm hover:file:bg-forge-800 cursor-pointer"
          />
          {file && <p className="text-slate-500 text-xs mt-1">{file.name} ({(file.size / 1024).toFixed(1)} KB)</p>}
        </div>

        {uploadError && <p className="text-red-400 text-sm">{uploadError}</p>}

        <Button
          onClick={handleUpload}
          disabled={!file || !selectedSubject || uploading}
        >
          {uploading ? <><Spinner size="sm" /> Uploading...</> : 'Upload'}
        </Button>
      </Card>

      <div>
        <h2 className="text-lg font-semibold text-slate-200 mb-3">Uploaded Materials</h2>
        <div className="space-y-2">
          {materials.length === 0 && (
            <p className="text-slate-500">No materials uploaded yet.</p>
          )}
          {materials.map((m) => (
            <Card key={m.id} className="flex items-center gap-3">
              <div className="flex-1">
                <p className="text-slate-200 text-sm font-medium">{m.filename}</p>
                <p className="text-slate-500 text-xs">{m.file_type?.toUpperCase()}</p>
              </div>
              <Badge color={STATUS_COLOR[m.parse_status] ?? 'slate'}>{m.parse_status}</Badge>
              {m.parse_status === 'pending' && (
                <Button size="sm" variant="secondary" onClick={() => handleParseNow(m.id)}>
                  Parse Now
                </Button>
              )}
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd frontend && npx vitest run src/test/Upload.test.jsx
```

Expected: 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/screens/Upload.jsx frontend/src/test/Upload.test.jsx
git commit -m "feat: Upload Material screen with file picker and parse status"
```

---

## Task 7: Study Session Screen

**Files:**
- Modify: `frontend/src/screens/StudySession.jsx`
- Create: `frontend/src/hooks/useSession.js`
- Create: `frontend/src/test/StudySession.test.jsx`

- [ ] **Step 1: Write failing tests**

Create `frontend/src/test/StudySession.test.jsx`:

```jsx
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
    await waitFor(() => expect(screen.getByText(/newton/i)).toBeInTheDocument())
  })

  it('submits answer and shows feedback', async () => {
    wrap(<StudySession />)
    await waitFor(() => screen.getByRole('button', { name: /start session/i }))
    fireEvent.click(screen.getByRole('button', { name: /start session/i }))
    await waitFor(() => screen.getByText(/newton/i))

    const textarea = screen.getByPlaceholderText(/your answer/i)
    await userEvent.type(textarea, 'Force equals mass times acceleration')
    fireEvent.click(screen.getByRole('button', { name: /submit/i }))

    await waitFor(() => expect(screen.getByText(/great answer/i)).toBeInTheDocument())
  })

  it('shows session summary after end', async () => {
    wrap(<StudySession />)
    await waitFor(() => screen.getByRole('button', { name: /start session/i }))
    fireEvent.click(screen.getByRole('button', { name: /start session/i }))
    await waitFor(() => screen.getByText(/newton/i))

    const textarea = screen.getByPlaceholderText(/your answer/i)
    await userEvent.type(textarea, 'F = ma')
    fireEvent.click(screen.getByRole('button', { name: /submit/i }))
    await waitFor(() => screen.getByText(/great answer/i))

    fireEvent.click(screen.getByRole('button', { name: /end session/i }))
    await waitFor(() => expect(screen.getByText(/session complete/i)).toBeInTheDocument())
    expect(screen.getByText('80%')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd frontend && npx vitest run src/test/StudySession.test.jsx
```

Expected: FAIL.

- [ ] **Step 3: Create `frontend/src/hooks/useSession.js`**

```js
import { useState } from 'react'
import { startSession, submitTurn, endSession } from '../api/client'

export function useSession() {
  const [state, setState] = useState('idle') // idle | active | ended | error
  const [session, setSession] = useState(null)   // { session_id, queue_length, current_ku, question }
  const [turns, setTurns] = useState([])         // { question, answer, result }
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
```

- [ ] **Step 4: Implement `frontend/src/screens/StudySession.jsx`**

```jsx
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

  return (
    <div className="max-w-2xl space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-slate-100">Study Session</h1>
        <div className="flex items-center gap-3">
          <span className="text-slate-500 text-sm">{turns.length} answered</span>
          <Button variant="ghost" size="sm" onClick={end}>End Session</Button>
        </div>
      </div>

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

      <Card>
        <textarea
          placeholder="Your answer..."
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && e.metaKey) handleSubmit() }}
          rows={4}
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
    </div>
  )
}
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd frontend && npx vitest run src/test/StudySession.test.jsx
```

Expected: 4 tests pass.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/screens/StudySession.jsx frontend/src/hooks/useSession.js frontend/src/test/StudySession.test.jsx
git commit -m "feat: Study Session screen with question/answer/feedback flow"
```

---

## Task 8: Learning Plan Screen

**Files:**
- Modify: `frontend/src/screens/LearningPlan.jsx`

> Note: No dedicated test file — plan display is a simple read-only view tested via manual verification. Integration with the API client is already covered in `client.test.js`.

- [ ] **Step 1: Implement `frontend/src/screens/LearningPlan.jsx`**

```jsx
import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getPlan, getSubject } from '../api/client'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Spinner from '../components/ui/Spinner'

export default function LearningPlan() {
  const { id } = useParams()
  const [plan, setPlan] = useState(null)
  const [subject, setSubject] = useState(null)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    Promise.all([getSubject(Number(id)), getPlan(Number(id))])
      .then(([s, p]) => {
        setSubject(s)
        setPlan(p)
      })
      .catch((e) => {
        if (e.status === 404) setNotFound(true)
      })
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="flex justify-center pt-20"><Spinner size="lg" /></div>

  if (notFound || !plan) {
    return (
      <div className="max-w-xl space-y-4">
        <h1 className="text-2xl font-bold text-slate-100">Learning Plan</h1>
        <Card>
          <p className="text-slate-400">No learning plan generated yet for {subject?.name ?? 'this subject'}.</p>
          <p className="text-slate-500 text-sm mt-2">Plans are generated by the nightly batch process after material is uploaded and parsed.</p>
        </Card>
        <Link to="/subjects">
          <Button variant="ghost">← Back to Subjects</Button>
        </Link>
      </div>
    )
  }

  let planData = {}
  let deadlines = {}
  let focusAreas = []
  try { planData = typeof plan.plan_data === 'string' ? JSON.parse(plan.plan_data) : plan.plan_data } catch {}
  try { deadlines = typeof plan.deadlines === 'string' ? JSON.parse(plan.deadlines) : plan.deadlines } catch {}
  try { focusAreas = typeof plan.focus_areas === 'string' ? JSON.parse(plan.focus_areas) : plan.focus_areas } catch {}

  return (
    <div className="max-w-2xl space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/subjects"><Button variant="ghost" size="sm">←</Button></Link>
        <h1 className="text-2xl font-bold text-slate-100">
          Learning Plan: {subject?.name}
        </h1>
      </div>

      {focusAreas?.length > 0 && (
        <Card>
          <h2 className="text-slate-300 font-semibold mb-3">Focus Areas</h2>
          <ul className="space-y-1">
            {focusAreas.map((area, i) => (
              <li key={i} className="text-slate-400 text-sm flex gap-2">
                <span className="text-forge-400">→</span>{area}
              </li>
            ))}
          </ul>
        </Card>
      )}

      <Card>
        <h2 className="text-slate-300 font-semibold mb-3">Plan</h2>
        <pre className="text-slate-400 text-sm whitespace-pre-wrap">{
          typeof planData === 'string' ? planData : JSON.stringify(planData, null, 2)
        }</pre>
      </Card>

      <p className="text-slate-600 text-xs">
        Last updated: {new Date(plan.generated_at).toLocaleString()}
      </p>
    </div>
  )
}
```

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/screens/LearningPlan.jsx
git commit -m "feat: Learning Plan screen showing plan data and focus areas"
```

---

## Task 9: Performance History Screen

**Files:**
- Modify: `frontend/src/screens/History.jsx`
- Create: `frontend/src/test/History.test.jsx`

- [ ] **Step 1: Write failing tests**

Create `frontend/src/test/History.test.jsx`:

```jsx
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd frontend && npx vitest run src/test/History.test.jsx
```

Expected: FAIL.

- [ ] **Step 3: Implement `frontend/src/screens/History.jsx`**

```jsx
import { useEffect, useState } from 'react'
import { getSubjects, getPerformance } from '../api/client'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import Spinner from '../components/ui/Spinner'

export default function History() {
  const [subjects, setSubjects] = useState([])
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [subjectFilter, setSubjectFilter] = useState('')

  useEffect(() => {
    getSubjects().then(setSubjects)
  }, [])

  useEffect(() => {
    setLoading(true)
    getPerformance(subjectFilter ? Number(subjectFilter) : undefined)
      .then(setRecords)
      .finally(() => setLoading(false))
  }, [subjectFilter])

  const total = records.length
  const correct = records.filter((r) => r.correct).length
  const accuracy = total > 0 ? Math.round((correct / total) * 100) : 0

  // Build daily accuracy chart data
  const byDay = {}
  records.forEach((r) => {
    const day = r.reviewed_at?.slice(0, 10) ?? 'unknown'
    if (!byDay[day]) byDay[day] = { day, correct: 0, total: 0 }
    byDay[day].total++
    if (r.correct) byDay[day].correct++
  })
  const chartData = Object.values(byDay)
    .sort((a, b) => a.day.localeCompare(b.day))
    .map((d) => ({ day: d.day, accuracy: Math.round((d.correct / d.total) * 100) }))

  return (
    <div className="max-w-4xl space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-100">Performance History</h1>
        <select
          value={subjectFilter}
          onChange={(e) => setSubjectFilter(e.target.value)}
          className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-slate-200 text-sm"
        >
          <option value="">All subjects</option>
          {subjects.map((s) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <Card>
          <p className="text-slate-400 text-sm">Reviews</p>
          <p className="text-3xl font-bold text-slate-200">{total}</p>
        </Card>
        <Card>
          <p className="text-slate-400 text-sm">Correct</p>
          <p className="text-3xl font-bold text-green-400">{correct}</p>
        </Card>
        <Card>
          <p className="text-slate-400 text-sm">Accuracy</p>
          <p className="text-3xl font-bold text-forge-400">{accuracy}%</p>
        </Card>
      </div>

      {chartData.length > 1 && (
        <Card>
          <h2 className="text-slate-300 font-semibold mb-4">Accuracy Over Time</h2>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="day" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                labelStyle={{ color: '#cbd5e1' }}
              />
              <Line type="monotone" dataKey="accuracy" stroke="#6366f1" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      )}

      <div>
        <h2 className="text-lg font-semibold text-slate-200 mb-3">Recent Reviews</h2>
        {loading && <div className="flex justify-center py-8"><Spinner /></div>}
        {!loading && records.length === 0 && (
          <p className="text-slate-500">No review history yet.</p>
        )}
        <div className="space-y-2">
          {records.slice(0, 50).map((r) => (
            <div key={r.id} className="flex items-center gap-3 px-4 py-3 bg-slate-800 rounded-lg border border-slate-700">
              <span className={`text-sm font-bold ${r.correct ? 'text-green-400' : 'text-red-400'}`}>
                {r.correct ? '✓' : '✗'}
              </span>
              <span className="flex-1 text-slate-300 text-sm">{r.ku_title}</span>
              <span className="text-slate-500 text-xs">Grade {r.grade ?? '—'}/5</span>
              <span className="text-slate-600 text-xs">{r.reviewed_at?.slice(0, 10)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd frontend && npx vitest run src/test/History.test.jsx
```

Expected: 3 tests pass.

- [ ] **Step 5: Run full test suite**

```bash
cd frontend && npx vitest run
```

Expected: All tests pass (client + Dashboard + SubjectLibrary + Upload + StudySession + History).

- [ ] **Step 6: Commit**

```bash
git add frontend/src/screens/History.jsx frontend/src/test/History.test.jsx
git commit -m "feat: Performance History screen with accuracy chart and review list"
```

---

## Task 10: Electron Main Process + FastAPI Integration

**Files:**
- Already created (Task 1): `frontend/electron/main.js`, `frontend/electron/server.js`, `frontend/electron/preload.js`

> This task verifies end-to-end Electron startup with the real FastAPI server running.

- [ ] **Step 1: Verify uvicorn is in the backend venv**

```bash
/Users/nelsbuhrley/ClaudeWorkspace/memoryforge/backend/.venv/bin/python -m uvicorn --version
```

Expected: `Running uvicorn X.X.X with CPython X.X.X on Darwin`

If missing:

```bash
cd /Users/nelsbuhrley/ClaudeWorkspace/memoryforge/backend && .venv/bin/pip install uvicorn
```

- [ ] **Step 2: Manually test FastAPI server starts via server.js path**

```bash
cd /Users/nelsbuhrley/ClaudeWorkspace/memoryforge/backend && \
  .venv/bin/python -m uvicorn memoryforge.api.app:create_app --factory --host 127.0.0.1 --port 9147
```

Expected: `Application startup complete. Uvicorn running on http://127.0.0.1:9147`

Stop with Ctrl+C.

- [ ] **Step 3: Test API is reachable**

```bash
curl http://127.0.0.1:9147/dashboard
```

Expected: JSON with `due_count`, `streak`, `streak_at_risk`, `subjects_summary`.

- [ ] **Step 4: Run the full Electron + Vite dev environment**

In one terminal:
```bash
cd frontend && npm run dev
```

Expected:
- Vite starts on `http://localhost:5173`
- Electron window opens showing the MemoryForge dashboard
- No console errors in DevTools

- [ ] **Step 5: Commit any fixes found during dev run**

```bash
git add -A && git commit -m "fix: Electron dev mode integration adjustments"
```

(Skip this step if no fixes needed.)

---

## Task 11: Final Build Verification

**Files:**
- Create or modify: `frontend/package.json` (electron-builder config, if needed)

- [ ] **Step 1: Add electron-builder config to `frontend/package.json`**

Add after `"private": true`:

```json
"build": {
  "appId": "com.memoryforge.app",
  "productName": "MemoryForge",
  "mac": {
    "target": "dmg",
    "category": "public.app-category.education"
  },
  "directories": {
    "output": "dist-electron"
  },
  "files": [
    "dist/**/*",
    "electron/**/*"
  ],
  "extraResources": [
    {
      "from": "../backend",
      "to": "backend",
      "filter": ["**/*", "!.venv/**/*", "!__pycache__/**/*"]
    }
  ]
}
```

- [ ] **Step 2: Run production Vite build**

```bash
cd frontend && npm run build
```

Expected: `dist/` built cleanly. No TypeScript or import errors.

- [ ] **Step 3: Run full test suite one final time**

```bash
cd frontend && npx vitest run
```

Expected: All tests pass.

- [ ] **Step 4: Final commit**

```bash
git add frontend/
git commit -m "feat: complete MemoryForge frontend — Electron + React + 6 screens"
```

- [ ] **Step 5: Push to remote**

```bash
git push origin main
```

Expected: Push succeeds.

---

## Summary

| Task | Files | Tests |
|------|-------|-------|
| 1. Scaffolding | 11 new files | Build verification |
| 2. API Client | `client.js` | 9 tests |
| 3. Layout + UI | 7 new components | Build verification |
| 4. Dashboard | `Dashboard.jsx` | 4 tests |
| 5. Subject Library | `SubjectLibrary.jsx` | 3 tests |
| 6. Upload | `Upload.jsx` | 3 tests |
| 7. Study Session | `StudySession.jsx` + hook | 4 tests |
| 8. Learning Plan | `LearningPlan.jsx` | Manual |
| 9. History | `History.jsx` | 3 tests |
| 10. Electron Integration | `main.js` + `server.js` | Manual dev run |
| 11. Final Build | electron-builder config | All tests + build |

**Total automated tests: 26**
