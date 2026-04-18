import React, { useState, useEffect, useCallback } from 'react'
import ScoreGauge from './components/ScoreGauge'
import SensorGrid, { SensorInfoDrawer, SENSOR_META } from './components/SensorCard'
import AISummary from './components/AISummary'
import './App.css'

const API_BASE = import.meta.env.VITE_API_URL || ''
const POLL_INTERVAL_MS = 2000

export default function App() {
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)
  const [lastFetch, setLastFetch] = useState(null)

  const [analysis, setAnalysis] = useState({ summary: '', flags: [] })
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [analysisError, setAnalysisError] = useState(null)

  const [activeSensorKey, setActiveSensorKey] = useState(null)

  const toggleSensorInfo = useCallback((key) => {
    setActiveSensorKey(prev => prev === key ? null : key)
  }, [])

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

  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, POLL_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [fetchStatus])

  const score = status?.score ?? 0
  const reading = status?.reading ?? null
  const connected = status?.connected ?? false

  return (
    <div className={`app ${activeSensorKey ? 'app--drawer-open' : ''}`}>
      <div className="app__content-wrapper">
        {/* ── Header ── */}
        <header className="app__header">
          <div className="app__brand">
            <div className="app__logo-mark">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9z" />
                <polyline points="9 22 9 12 15 12 15 22" />
              </svg>
            </div>
            <h1 className="app__title">RoomPulse</h1>
          </div>

          <div className="app__header-right">
            <div className="app__status-pill">
              <span className={`app__status-dot ${connected ? 'app__status-dot--on' : 'app__status-dot--off'}`} />
              {connected ? 'Live' : 'Offline'}
            </div>
            {lastFetch && (
              <span className="app__last-update">
                {lastFetch.toLocaleTimeString()}
              </span>
            )}
          </div>
        </header>

        {error && (
          <div className="app__error" role="alert" id="error-banner">
            {error}
          </div>
        )}

        <main className="app__main">
          {/* ── Hero row ── */}
          <div className="app__hero">
            <ScoreGauge score={score} />
            <AISummary
              summary={analysis.summary}
              flags={analysis.flags}
              loading={analysisLoading}
              error={analysisError}
              onRefresh={fetchAnalysis}
            />
          </div>

          {/* ── Attribute cards ── */}
          <section>
            <h2 className="app__section-label">Your Environment</h2>
            <SensorGrid 
              reading={reading} 
              onInfoClick={toggleSensorInfo}
            />
          </section>
        </main>

        <footer className="app__footer">
          RoomPulse · HackAugie 2026
        </footer>
      </div>

      {activeSensorKey && (
        <SensorInfoDrawer
          meta={SENSOR_META[activeSensorKey]}
          value={reading ? reading[activeSensorKey] : null}
          onClose={() => setActiveSensorKey(null)}
        />
      )}
    </div>
  )
}
