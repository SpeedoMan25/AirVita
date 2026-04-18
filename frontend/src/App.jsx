import React, { useState, useEffect, useCallback } from 'react'
import ScoreGauge from './components/ScoreGauge'
import SensorGrid from './components/SensorCard'
import AISummary from './components/AISummary'
import ScenarioControls from './components/ScenarioControls'
import CalculationMath from './components/CalculationMath'
import './App.css'

const API_BASE = import.meta.env.VITE_API_URL || ''
const POLL_INTERVAL_MS = 2000

export default function App() {
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)
  const [lastFetch, setLastFetch] = useState(null)

  // Scenarios state
  const [scenarios, setScenarios] = useState([])
  const [manualScenarioId, setManualScenarioId] = useState(null)

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

  const fetchScenarios = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/scenarios`)
      if (res.ok) {
        const data = await res.json()
        setScenarios(data)
      }
    } catch (err) {
      console.error('Failed to fetch scenarios:', err)
    }
  }, [])

  const selectScenario = async (id) => {
    try {
      setManualScenarioId(id)
      await fetch(`${API_BASE}/api/scenarios/select`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id })
      })
      fetchStatus() // Immediate update
    } catch (err) {
      console.error('Failed to select scenario:', err)
    }
  }

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

  // Initial fetch
  useEffect(() => {
    fetchStatus()
    fetchScenarios()
    const interval = setInterval(fetchStatus, POLL_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [fetchStatus, fetchScenarios])

  const score = status?.score ?? 0
  const reading = status?.reading ?? null
  const breakdown = status?.breakdown ?? null
  const connected = status?.connected ?? false

  return (
    <div className="app">
      {/* Header — left aligned, compact */}
      <header className="app__header">
        <div className="app__logo">
          <h1 className="app__title">RoomPulse</h1>
        </div>
        <p className="app__subtitle">Neural IAQ Monitoring</p>
      </header>

      {/* Error banner */}
      {error && (
        <div className="app__error" role="alert" id="error-banner">
          {error}
        </div>
      )}

      {/* Main Dashboard */}
      <main className="app__main">
        {/* Top row: Score gauge + AI analysis + Math side by side */}
        <div className="app__top-row">
          <div className="app__column">
             <ScoreGauge score={score} connected={connected} />
             <CalculationMath breakdown={breakdown} />
          </div>
          
          <div className="app__column">
            <AISummary
              summary={analysis.summary}
              flags={analysis.flags}
              loading={analysisLoading}
              error={analysisError}
              onRefresh={fetchAnalysis}
            />
            <ScenarioControls 
              scenarios={scenarios} 
              activeId={manualScenarioId}
              onSelect={selectScenario}
            />
          </div>
        </div>

        {/* Sensor readings section */}
        <div>
          <div className="app__section-header">
            <h2 className="app__section-title">Real-Time Sensors</h2>
          </div>
          <SensorGrid reading={reading} />
        </div>
      </main>

      {/* Footer */}
      <footer className="app__footer">
        <span>RoomPulse v1.1 • Neural Engine</span>
        {lastFetch && (
          <span className="app__last-update">
            Live Stream: {lastFetch.toLocaleTimeString()}
          </span>
        )}
      </footer>
    </div>
  )
}
