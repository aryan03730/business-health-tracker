import { Link, Route, Routes } from 'react-router-dom'
import Home from './pages/Home'
import Wizard from './pages/Wizard'
import Dashboard from './pages/Dashboard'

export default function App() {
  return (
    <div className="shell">
      <header className="topbar">
        <Link to="/" className="brand">
          <span className="brand-dot" aria-hidden="true" />
          Business Health Tracker
        </Link>
      </header>
      <main className="page">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/new" element={<Wizard />} />
          <Route path="/s/:id" element={<Dashboard />} />
          <Route path="/s/:id/edit" element={<Wizard />} />
          <Route
            path="*"
            element={
              <div className="card">
                <h1 className="title">Page not found</h1>
                <Link className="btn btn-primary" to="/">Go home</Link>
              </div>
            }
          />
        </Routes>
      </main>
    </div>
  )
}
