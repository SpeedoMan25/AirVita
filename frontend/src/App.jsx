import React, { useState, useEffect, useCallback } from 'react'
import ScoreGauge from './components/ScoreGauge'
import SleepScoreGauge from './components/SleepScoreGauge'
import SensorGrid, { SensorInfoDrawer, SENSOR_META } from './components/SensorCard'
import AISummary from './components/AISummary'
import ScenarioControls from './components/ScenarioControls'
import CalculationMath from './components/CalculationMath'
import RoomScanner from './components/RoomScanner'
import MobilePairing from './components/MobilePairing'
import './App.css'

const API_BASE = import.meta.env.DEV
  ? `http://${window.location.hostname}:8000`
  : import.meta.env.VITE_API_URL || '';
const POLL_INTERVAL_MS = 2000

export default function App() {
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)
  const [lastFetch, setLastFetch] = useState(null)

  // Simulation/Scenarios state (from model branch)
  const [scenarios, setScenarios] = useState([])
  const [manualScenarioId, setManualScenarioId] = useState(null)

  // AI analysis state
  const [analysis, setAnalysis] = useState({ summary: '', flags: [] })
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [analysisError, setAnalysisError] = useState(null)

  // Drawer state (from origin/main)
  const [activeSensorKey, setActiveSensorKey] = useState(null)
  const [isTechOpen, setIsTechOpen] = useState(false)
  const [isScannerOpen, setIsScannerOpen] = useState(false)
  const [isPairingOpen, setIsPairingOpen] = useState(false)
  const [unitSystem, setUnitSystem] = useState('metric') // 'metric' or 'imperial'

  const toggleSensorInfo = useCallback((key) => {
    setActiveSensorKey(prev => prev === key ? null : key)
    if (key) setIsTechOpen(false) // Close tech when info opens
  }, [])

  const toggleTechDrawer = () => {
    setIsTechOpen(prev => !prev)
    if (!isTechOpen) setActiveSensorKey(null) // Close info when tech opens
  }

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

  // Combined effect — Status polling + Scenarios fetching
  useEffect(() => {
    fetchStatus()
    fetchScenarios()
    const interval = setInterval(fetchStatus, POLL_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [fetchStatus, fetchScenarios])

  const score = status?.score ?? 0
  const sleepScore = status?.sleep_score ?? 0
  const reading = status?.reading ?? null
  const breakdown = status?.breakdown ?? null
  const connected = status?.connected ?? false

  return (
    <div className={`app ${activeSensorKey ? 'app--drawer-open' : ''} ${isTechOpen ? 'app--tech-open' : ''}`}>
      <div className="app__content-wrapper">
        <header className="app__header">
          <div className="app__brand">
            <button 
              className={`app__tech-toggle ${isTechOpen ? 'app__tech-toggle--active' : ''}`}
              onClick={toggleTechDrawer}
              title="Neural Engine Settings"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ width: '20px', height: '20px' }}>
                <circle cx="12" cy="12" r="3" />
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1Z" />
              </svg>
            </button>
            <div className="app__logo-mark">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9z" />
                <polyline points="9 22 9 12 15 12 15 22" />
              </svg>
            </div>
            <h1 className="app__title">RoomPulse</h1>
          </div>

          <div className="app__header-right">
            <button 
              className="app__scanner-toggle"
              onClick={() => setIsPairingOpen(true)}
              title="Pair Phone via QR Code"
              style={{ padding: '8px 12px' }}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ width: '18px', height: '18px' }}>
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <rect x="7" y="7" width="3" height="3"/>
                <rect x="14" y="7" width="3" height="3"/>
                <rect x="7" y="14" width="3" height="3"/>
                <rect x="14" y="14" width="3" height="3"/>
              </svg>
            </button>
            
            <button 
              className={`app__scanner-toggle ${isScannerOpen ? 'app__scanner-toggle--active' : ''}`}
              onClick={() => setIsScannerOpen(!isScannerOpen)}
              title="Open Scanner Camera"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ width: '18px', height: '18px' }}>
                <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                <circle cx="12" cy="13" r="4" />
              </svg>
              <span>Scan</span>
            </button>

            <div className="app__unit-toggle">
              <button 
                className={`app__unit-btn ${unitSystem === 'metric' ? 'app__unit-btn--active' : ''}`}
                onClick={() => setUnitSystem('metric')}
              >
                Metric
              </button>
              <button 
                className={`app__unit-btn ${unitSystem === 'imperial' ? 'app__unit-btn--active' : ''}`}
                onClick={() => setUnitSystem('imperial')}
              >
                Imperial
              </button>
            </div>
            
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

        {/* Error banner */}
        {error && (
          <div className="app__error" role="alert" id="error-banner">
            {error}
          </div>
        )}

        {/* Main Dashboard Layout */}
        <main className="app__main">
          {/* Hero Row: Gauges + AI Summary */}
          <div className="app__hero">
            <div className="app__gauges">
              <ScoreGauge score={score} />
              <SleepScoreGauge score={sleepScore} />
            </div>
            <AISummary
              summary={analysis.summary}
              flags={analysis.flags}
              loading={analysisLoading}
              error={analysisError}
              onRefresh={fetchAnalysis}
            />
          </div>

          {/* Sensor Readings section */}
          <section className="app__sensors">
            <h2 className="app__section-label">Real-Time Sensors</h2>
            <SensorGrid 
              reading={reading} 
              onInfoClick={toggleSensorInfo}
              unitSystem={unitSystem}
            />
          </section>
        </main>

        <footer className="app__footer">
          RoomPulse v1.3 · Neural Engine · HackAugie 2026
        </footer>
      </div>

      {/* Tech Drawer (Left) */}
      {isTechOpen && (
        <aside className="app__tech-drawer">
          <button className="app__tech-drawer-close" onClick={() => setIsTechOpen(false)}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ width: '20px', height: '20px' }}>
              <path d="M18 6 6 18" /><path d="m6 6 12 12" />
            </svg>
          </button>
          <div className="app__tech-drawer-header">
            <div className="app__tech-drawer-icon">🛠️</div>
            <div>
              <h3>Neural Engine</h3>
              <p>Simulations & Scoring</p>
            </div>
          </div>
          <div className="app__tech-drawer-body">
            <CalculationMath breakdown={breakdown} />
            <ScenarioControls 
              scenarios={scenarios} 
              activeId={manualScenarioId}
              onSelect={selectScenario}
            />
          </div>
        </aside>
      )}

      {/* Info Drawer (from origin/main) */}
      {activeSensorKey && (
        <SensorInfoDrawer
          meta={SENSOR_META[activeSensorKey]}
          value={reading ? reading[activeSensorKey] : null}
          onClose={() => setActiveSensorKey(null)}
          unitSystem={unitSystem}
        />
      )}

      {/* Room Classification Scanner */}
      {isScannerOpen && (
        <RoomScanner onClose={() => setIsScannerOpen(false)} />
      )}

      {/* Mobile QR Pairing */}
      {isPairingOpen && (
        <MobilePairing onClose={() => setIsPairingOpen(false)} />
      )}
    </div>
  )
}

