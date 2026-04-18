import React, { useState, useEffect, useCallback } from 'react'
import ScoreGauge from './components/ScoreGauge'
import SensorGrid from './components/SensorCard'
import './App.css'

const API_BASE = import.meta.env.VITE_API_URL || ''
const POLL_INTERVAL_MS = 2000

export default function App() {
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)
  const [lastFetch, setLastFetch] = useState(null)

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

  // Poll the backend every POLL_INTERVAL_MS
  useEffect(() => {
    fetchStatus() // Initial fetch
    const interval = setInterval(fetchStatus, POLL_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [fetchStatus])

  const score = status?.score ?? 0
  const reading = status?.reading ?? null
  const connected = status?.connected ?? false

  return (
    <div className="app">
      {/* Header */}
      <header className="app__header">
        <div className="app__logo">
          <span className="app__logo-icon">🌿</span>
          <h1 className="app__title">RoomPulse</h1>
        </div>
        <p className="app__subtitle">Real-time Room Environment Monitor</p>
      </header>

      {/* Error banner */}
      {error && (
        <div className="app__error" role="alert" id="error-banner">
          {error}
        </div>
      )}

      {/* Main Dashboard */}
      <main className="app__main">
        {/* Score Gauge */}
        <ScoreGauge score={score} connected={connected} />

        <hr className="app__divider" />
        <h2 className="app__section-title">Sensor Readings</h2>

        {/* Sensor Cards Grid */}
        <SensorGrid reading={reading} />
      </main>

      {/* Footer */}
      <footer className="app__footer">
        {lastFetch && (
          <p className="app__last-update">
            Last updated: {lastFetch.toLocaleTimeString()}
          </p>
        )}
        <p>RoomPulse v1.0 — HackAugie 2026</p>
      </footer>
    </div>
  )
}
