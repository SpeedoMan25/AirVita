import React, { useState, useEffect, useCallback } from 'react'
import ScoreGauge from './components/ScoreGauge'
import SensorGrid from './components/SensorCard'
import AISummary from './components/AISummary'
import './App.css'

const API_BASE = import.meta.env.VITE_API_URL || ''
const POLL_INTERVAL_MS = 2000

export default function App() {
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)
  const [lastFetch, setLastFetch] = useState(null)

  // AI analysis state
  const [analysis, setAnalysis] = useState({ summary: '', flags: [] })
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [analysisError, setAnalysisError] = useState(null)

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/current-status`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setStatus(data)
      setError(null)
      setLastFetch(new Date())
    } catch (err) {
      setError(`Unable to reach backend: ${err.message}`)
    }
  }, [])

  const fetchAnalysis = useCallback(async () => {
    setAnalysisLoading(true)
    setAnalysisError(null)
    try {
      const res = await fetch(`${API_BASE}/api/analyze`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setAnalysis(data)
    } catch (err) {
      setAnalysisError(`Analysis failed: ${err.message}`)
    } finally {
      setAnalysisLoading(false)
    }
  }, [])

  // Poll the backend every POLL_INTERVAL_MS
  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, POLL_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [fetchStatus])

  const score = status?.score ?? 0
  const reading = status?.reading ?? null
  const connected = status?.connected ?? false

  return (
    <div className="app">
      {/* Header — left aligned, compact */}
      <header className="app__header">
        <div className="app__logo">
          <h1 className="app__title">RoomPulse</h1>
        </div>
        <p className="app__subtitle">Environment Monitor</p>
      </header>

      {/* Error banner */}
      {error && (
        <div className="app__error" role="alert" id="error-banner">
          {error}
        </div>
      )}

      {/* Main Dashboard */}
      <main className="app__main">
        {/* Top row: Score gauge + AI analysis side by side */}
        <div className="app__top-row">
          <ScoreGauge score={score} connected={connected} />
          <AISummary
            summary={analysis.summary}
            flags={analysis.flags}
            loading={analysisLoading}
            error={analysisError}
            onRefresh={fetchAnalysis}
          />
        </div>

        {/* Sensor readings section */}
        <div>
          <div className="app__section-header">
            <h2 className="app__section-title">Sensors</h2>
            <span className="app__section-count">7</span>
          </div>
          <SensorGrid reading={reading} />
        </div>
      </main>

      {/* Footer */}
      <footer className="app__footer">
        <span>RoomPulse v1.0</span>
        {lastFetch && (
          <span className="app__last-update">
            Updated {lastFetch.toLocaleTimeString()}
          </span>
        )}
      </footer>
    </div>
  )
}
