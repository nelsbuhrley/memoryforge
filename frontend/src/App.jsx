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
