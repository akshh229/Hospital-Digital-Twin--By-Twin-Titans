import { Suspense, lazy } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const PatientDetail = lazy(() => import('./pages/PatientDetail'))

function RouteFallback() {
  return (
    <div className="card">
      <h2 className="text-lazarus-text font-semibold mb-2">Loading view</h2>
      <p className="text-sm text-lazarus-muted">Preparing the latest patient telemetry and charts.</p>
    </div>
  )
}

function App() {
  return (
    <Router>
      <Layout>
        <Suspense fallback={<RouteFallback />}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/patient/:patientId" element={<PatientDetail />} />
          </Routes>
        </Suspense>
      </Layout>
    </Router>
  )
}

export default App
