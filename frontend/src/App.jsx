import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import {
  Activity, Thermometer, Droplets, Sun, Volume2, Gauge, Wind,
  Heart, Moon, Book, Briefcase, Sparkles, Settings2, Info, X,
  RefreshCw, AlertCircle, LayoutDashboard, BrainCircuit, Zap,
  CheckCircle2, ChevronRight, Camera
} from 'lucide-react'
import { AreaChart, Area, ResponsiveContainer, YAxis, XAxis, Tooltip } from 'recharts'

import RoomScanner from './components/RoomScanner'
import MobilePairing from './components/MobilePairing'


const API_BASE = '';
const POLL_INTERVAL_MS = 2000

/* ═══════════════════════════════════════════════════
   SENSOR & ACTIVITY METADATA
   ═══════════════════════════════════════════════════ */

const SENSOR_META = {
  temperature_c: {
    label: 'Temperature', unit: '°C', icon: Thermometer,
    iconColor: '#f97316', iconBg: '#fff7ed', iconBorder: '#fed7aa',
    sparkColor: '#f97316', sparkFill: '#fff7ed',
    min: 10, max: 40,
    getStatus: v => v < 18 ? 'Cold' : v < 20 ? 'Cool' : v <= 24 ? 'Ideal' : v <= 28 ? 'Warm' : 'Hot',
    ranges: [
      { label: 'Cold', max: 18, color: '#3b82f6', text: 'Risk of discomfort, muscles tense up.' },
      { label: 'Cool', max: 20, color: '#60a5fa', text: 'Slightly below ideal. Fine with layers.' },
      { label: 'Ideal', max: 24, color: '#10b981', text: 'Optimal for health, sleep, and focus.' },
      { label: 'Warm', max: 28, color: '#f59e0b', text: 'Comfortable, but productivity may dip.' },
      { label: 'Hot', max: 40, color: '#f43f5e', text: 'Increased fatigue, dehydration risk.' },
    ],
  },
  humidity_pct: {
    label: 'Humidity', unit: '%', icon: Droplets,
    iconColor: '#3b82f6', iconBg: '#eff6ff', iconBorder: '#bfdbfe',
    sparkColor: '#3b82f6', sparkFill: '#eff6ff',
    min: 0, max: 100,
    getStatus: v => v < 30 ? 'Dry' : v < 40 ? 'Low' : v <= 60 ? 'Balanced' : v <= 70 ? 'Humid' : 'Damp',
    ranges: [
      { label: 'Dry', max: 30, color: '#f59e0b', text: 'Skin irritation, static electricity.' },
      { label: 'Low', max: 40, color: '#60a5fa', text: 'Slightly dry; acceptable short-term.' },
      { label: 'Balanced', max: 60, color: '#10b981', text: 'Ideal range for comfort and health.' },
      { label: 'Humid', max: 70, color: '#f59e0b', text: 'Muggy feeling, mold risk increases.' },
      { label: 'Damp', max: 100, color: '#f43f5e', text: 'High mold risk, condensation likely.' },
    ],
  },
  light_lux: {
    label: 'Light', unit: 'lux', icon: Sun,
    iconColor: '#f59e0b', iconBg: '#fffbeb', iconBorder: '#fde68a',
    sparkColor: '#f59e0b', sparkFill: '#fffbeb',
    min: 0, max: 1000,
    getStatus: v => v < 100 ? 'Dim' : v < 300 ? 'Low' : v <= 500 ? 'Optimal' : v <= 800 ? 'Bright' : 'Intense',
    ranges: [
      { label: 'Dim', max: 100, color: '#6366f1', text: 'Good for sleep and relaxation.' },
      { label: 'Low', max: 300, color: '#60a5fa', text: 'Casual activities, reading may strain.' },
      { label: 'Optimal', max: 500, color: '#10b981', text: 'Ideal for focused work and study.' },
      { label: 'Bright', max: 800, color: '#f59e0b', text: 'Energizing, but may cause glare.' },
      { label: 'Intense', max: 1000, color: '#f43f5e', text: 'Eye fatigue possible over time.' },
    ],
  },
  noise_db: {
    label: 'Noise', unit: 'dB', icon: Volume2,
    iconColor: '#a855f7', iconBg: '#faf5ff', iconBorder: '#e9d5ff',
    sparkColor: '#a855f7', sparkFill: '#faf5ff',
    min: 0, max: 100,
    getStatus: v => v < 30 ? 'Silent' : v < 45 ? 'Quiet' : v <= 55 ? 'Moderate' : v <= 70 ? 'Loud' : 'Noisy',
    ranges: [
      { label: 'Silent', max: 30, color: '#10b981', text: 'Perfect for sleep and deep focus.' },
      { label: 'Quiet', max: 45, color: '#60a5fa', text: 'Library-level. Great for concentration.' },
      { label: 'Moderate', max: 55, color: '#f59e0b', text: 'Normal conversation level.' },
      { label: 'Loud', max: 70, color: '#f97316', text: 'Sustained exposure causes stress.' },
      { label: 'Noisy', max: 100, color: '#f43f5e', text: 'Hearing protection recommended.' },
    ],
  },
  pressure_hpa: {
    label: 'Pressure', unit: 'hPa', icon: Gauge,
    iconColor: '#10b981', iconBg: '#ecfdf5', iconBorder: '#a7f3d0',
    sparkColor: '#10b981', sparkFill: '#ecfdf5',
    min: 960, max: 1060,
    getStatus: v => v < 1000 ? 'Low' : v <= 1025 ? 'Normal' : 'High',
    ranges: [
      { label: 'Low', max: 1000, color: '#6366f1', text: 'Storm system likely. Headaches possible.' },
      { label: 'Normal', max: 1025, color: '#10b981', text: 'Stable conditions. No weather impact.' },
      { label: 'High', max: 1060, color: '#f59e0b', text: 'Clear skies. Dry air may increase.' },
    ],
  },
  pm25_ugm3: {
    label: 'PM 2.5', unit: 'µg/m³', icon: Wind,
    iconColor: '#f43f5e', iconBg: '#fff1f2', iconBorder: '#fecdd3',
    sparkColor: '#f43f5e', sparkFill: '#fff1f2',
    min: 0, max: 150,
    getStatus: v => v < 12 ? 'Clean' : v < 35 ? 'Moderate' : v < 55 ? 'Unhealthy' : 'Poor',
    ranges: [
      { label: 'Clean', max: 12, color: '#10b981', text: 'Excellent air. Safe for all groups.' },
      { label: 'Moderate', max: 35, color: '#f59e0b', text: 'Acceptable. Sensitive people may react.' },
      { label: 'Unhealthy', max: 55, color: '#f97316', text: 'Limit prolonged outdoor exertion.' },
      { label: 'Poor', max: 150, color: '#f43f5e', text: 'Health risk. Use air purification.' },
    ],
  },
  voc_ppb: {
    label: 'VOC', unit: 'ppb', icon: Activity,
    iconColor: '#14b8a6', iconBg: '#f0fdfa', iconBorder: '#99f6e4',
    sparkColor: '#14b8a6', sparkFill: '#f0fdfa',
    min: 0, max: 1500,
    getStatus: v => v < 300 ? 'Fresh' : v < 500 ? 'Acceptable' : v < 1000 ? 'Elevated' : 'Poor',
    ranges: [
      { label: 'Fresh', max: 300, color: '#14b8a6', text: 'Clean, outdoor-quality air.' },
      { label: 'Acceptable', max: 500, color: '#3b82f6', text: 'Safe for long-term exposure.' },
      { label: 'Elevated', max: 1000, color: '#f59e0b', text: 'Increased irritation possible.' },
      { label: 'Poor', max: 1500, color: '#f43f5e', text: 'Immediate ventilation recommended.' },
    ],
  }
}

const ACTIVITY_META = {
  health: {
    label: 'Overall Health', icon: Heart, color: '#10b981', sub: 'Environment Balance',
    unit: 'pts', iconColor: '#10b981', iconBg: '#ecfdf5', iconBorder: '#a7f3d0',
    ranges: [
      { label: 'Critical', max: 25, color: '#f43f5e', text: 'Severe environmental issues detected.' },
      { label: 'Poor', max: 50, color: '#f97316', text: 'Multiple factors need improvement.' },
      { label: 'Fair', max: 70, color: '#f59e0b', text: 'Acceptable but room for improvement.' },
      { label: 'Good', max: 85, color: '#10b981', text: 'Healthy environment for all activities.' },
      { label: 'Excellent', max: 100, color: '#059669', text: 'Optimal conditions across all metrics.' },
    ],
    getStatus: v => v < 25 ? 'Critical' : v < 50 ? 'Poor' : v < 70 ? 'Fair' : v < 85 ? 'Good' : 'Excellent',
  },
  sleep: {
    label: 'Sleep Quality', icon: Moon, color: '#6366f1', sub: 'Restorative Potential',
    unit: 'pts', iconColor: '#6366f1', iconBg: '#eef2ff', iconBorder: '#c7d2fe',
    ranges: [
      { label: 'Restless', max: 30, color: '#f43f5e', text: 'Too noisy, bright, or warm for sleep.' },
      { label: 'Disturbed', max: 50, color: '#f97316', text: 'Intermittent disruptions likely.' },
      { label: 'Adequate', max: 70, color: '#f59e0b', text: 'Sleep possible, but not restorative.' },
      { label: 'Restful', max: 85, color: '#6366f1', text: 'Good conditions for deep sleep.' },
      { label: 'Optimal', max: 100, color: '#4f46e5', text: 'Dark, cool, quiet — perfect for sleep.' },
    ],
    getStatus: v => v < 30 ? 'Restless' : v < 50 ? 'Disturbed' : v < 70 ? 'Adequate' : v < 85 ? 'Restful' : 'Optimal',
  },
  study: {
    label: 'Study Focus', icon: Book, color: '#f59e0b', sub: 'Cognitive Load',
    unit: 'pts', iconColor: '#f59e0b', iconBg: '#fffbeb', iconBorder: '#fde68a',
    ranges: [
      { label: 'Distracted', max: 30, color: '#f43f5e', text: 'Environment hinders concentration.' },
      { label: 'Unfocused', max: 50, color: '#f97316', text: 'Frequent attention breaks expected.' },
      { label: 'Moderate', max: 70, color: '#f59e0b', text: 'Functional but not ideal for deep work.' },
      { label: 'Focused', max: 85, color: '#10b981', text: 'Good lighting, low noise. Productive.' },
      { label: 'Flow State', max: 100, color: '#059669', text: 'Peak conditions for deep learning.' },
    ],
    getStatus: v => v < 30 ? 'Distracted' : v < 50 ? 'Unfocused' : v < 70 ? 'Moderate' : v < 85 ? 'Focused' : 'Flow State',
  },
  work: {
    label: 'Work Flow', icon: Briefcase, color: '#3b82f6', sub: 'Steady Productivity',
    unit: 'pts', iconColor: '#3b82f6', iconBg: '#eff6ff', iconBorder: '#bfdbfe',
    ranges: [
      { label: 'Blocked', max: 30, color: '#f43f5e', text: 'Environment actively disrupts workflow.' },
      { label: 'Struggling', max: 50, color: '#f97316', text: 'Productivity significantly hampered.' },
      { label: 'Steady', max: 70, color: '#f59e0b', text: 'Manageable but comfort improvements help.' },
      { label: 'Productive', max: 85, color: '#3b82f6', text: 'Comfortable, well-lit, focused space.' },
      { label: 'Peak', max: 100, color: '#1d4ed8', text: 'Ideal temperature, light, and air quality.' },
    ],
    getStatus: v => v < 30 ? 'Blocked' : v < 50 ? 'Struggling' : v < 70 ? 'Steady' : v < 85 ? 'Productive' : 'Peak',
  },
  fun: {
    label: 'Social Energy', icon: Sparkles, color: '#f43f5e', sub: 'Vibrant Atmosphere',
    unit: 'pts', iconColor: '#f43f5e', iconBg: '#fff1f2', iconBorder: '#fecdd3',
    ranges: [
      { label: 'Dull', max: 30, color: '#94a3b8', text: 'Environment feels flat and uninviting.' },
      { label: 'Subdued', max: 50, color: '#f59e0b', text: 'Lacks vibrancy for social activities.' },
      { label: 'Pleasant', max: 70, color: '#10b981', text: 'Comfortable for casual socializing.' },
      { label: 'Vibrant', max: 85, color: '#f43f5e', text: 'Lively, warm, and engaging atmosphere.' },
      { label: 'Electric', max: 100, color: '#e11d48', text: 'Peak social energy. Great for hosting.' },
    ],
    getStatus: v => v < 30 ? 'Dull' : v < 50 ? 'Subdued' : v < 70 ? 'Pleasant' : v < 85 ? 'Vibrant' : 'Electric',
  }
}

const CONVERSIONS = {
  temperature_c: {
    imperial: { unit: '°F', convert: v => (v * 9 / 5) + 32 },
    metric: { unit: '°C', convert: v => v }
  },
  pressure_hpa: {
    imperial: { unit: 'inHg', convert: v => v * 0.02953 },
    metric: { unit: 'hPa', convert: v => v }
  }
}

/* ═══════════════════════════════════════════════════
   SEMI-CIRCLE GAUGE COMPONENT
   ═══════════════════════════════════════════════════ */

function SemiGauge({ value, label, sub, color, activityKey, isSelected, onSelect }) {
  const clamped = Math.min(100, Math.max(0, value))
  const r = 40
  const totalArc = Math.PI * r
  const filled = (clamped / 100) * totalArc
  const meta = ACTIVITY_META[activityKey] || {}

  return (
    <div
      onClick={() => onSelect(`activity_${activityKey}`)}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: isSelected ? '19px 15px' : '20px 16px',
        borderRadius: '20px',
        border: isSelected ? `2px solid ${color}` : '1px solid #e2e8f0',
        background: '#ffffff',
        boxShadow: isSelected ? `0 0 0 3px ${meta.iconBg || '#f1f5f9'}` : '0 1px 3px rgba(0,0,0,0.04)',
        position: 'relative',
        minWidth: '140px',
        cursor: 'pointer',
        transition: 'border 0.2s ease, box-shadow 0.2s ease',
      }}
    >
      {/* Info hint */}
      <div style={{
        position: 'absolute', top: '10px', right: '10px',
        color: isSelected ? color : '#cbd5e1',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <Info size={14} />
      </div>

      {/* SVG Gauge */}
      <div style={{ position: 'relative', width: '120px', height: '70px' }}>
        <svg viewBox="0 0 100 60" style={{ width: '100%', height: '100%' }}>
          <path d="M 10 55 A 40 40 0 0 1 90 55" fill="none" stroke="#f1f5f9" strokeWidth="8" strokeLinecap="round" />
          <path d="M 10 55 A 40 40 0 0 1 90 55" fill="none" stroke={color} strokeWidth="8" strokeLinecap="round"
            strokeDasharray={totalArc} strokeDashoffset={totalArc - filled}
            style={{ transition: 'stroke-dashoffset 1s ease-out' }}
          />
        </svg>
        <div style={{
          position: 'absolute', inset: 0,
          display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'flex-end',
          paddingBottom: '2px',
        }}>
          <span style={{ fontSize: '28px', fontWeight: 900, color: '#1e293b', lineHeight: 1 }}>
            {Math.round(value)}
          </span>
        </div>
      </div>

      {/* Label */}
      <div style={{ marginTop: '8px', textAlign: 'center' }}>
        <div style={{ fontSize: '13px', fontWeight: 700, color: '#334155' }}>{label}</div>
        <div style={{ fontSize: '11px', fontWeight: 500, color: '#94a3b8', marginTop: '2px' }}>{sub}</div>
      </div>
    </div>
  )
}

/* ═══════════════════════════════════════════════════
   ANIMATED NUMBER — smooth value transitions
   ═══════════════════════════════════════════════════ */

function AnimatedNumber({ value, decimals = 1 }) {
  const [displayed, setDisplayed] = useState(value)
  const prevRef = useRef(value)
  const frameRef = useRef(null)

  useEffect(() => {
    const from = prevRef.current
    const to = typeof value === 'number' ? value : parseFloat(value)
    if (isNaN(to)) { setDisplayed(value); return }
    prevRef.current = to
    const duration = 600
    const start = performance.now()
    const animate = (now) => {
      const elapsed = now - start
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3) // ease-out cubic
      setDisplayed((from + (to - from) * eased).toFixed(decimals))
      if (progress < 1) frameRef.current = requestAnimationFrame(animate)
    }
    frameRef.current = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(frameRef.current)
  }, [value, decimals])

  return <>{displayed}</>
}

/* ═══════════════════════════════════════════════════
   SENSOR STATUS CARD COMPONENT
   ═══════════════════════════════════════════════════ */

function StatusCard({ sensorKey, value, history, unitSystem, onSelect, isSelected }) {
  const meta = SENSOR_META[sensorKey]
  const IconComp = meta.icon

  const numericVal = useMemo(() => {
    if (value === null || value === undefined) return null
    const conv = CONVERSIONS[sensorKey]?.[unitSystem]
    return conv ? conv.convert(value) : value
  }, [value, sensorKey, unitSystem])

  const displayVal = numericVal !== null ? numericVal : '—'
  const unit = CONVERSIONS[sensorKey]?.[unitSystem]?.unit || meta.unit
  const status = value != null ? meta.getStatus(value) : null

  return (
    <div
      onClick={() => onSelect(sensorKey)}
      style={{
        background: '#ffffff',
        border: isSelected ? `2px solid ${meta.iconColor}` : '1px solid #e2e8f0',
        borderRadius: '16px',
        padding: isSelected ? '23px' : '24px', /* compensate for thicker border */
        boxShadow: isSelected ? `0 0 0 3px ${meta.iconBg}` : '0 1px 3px rgba(0,0,0,0.04)',
        position: 'relative',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        minHeight: '200px',
        cursor: 'pointer',
        transition: 'border 0.2s ease, box-shadow 0.2s ease',
      }}
    >
      {/* Header row: icon + info hint */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div style={{
          padding: '10px', borderRadius: '14px',
          background: meta.iconBg, border: `1px solid ${meta.iconBorder}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <IconComp size={20} color={meta.iconColor} />
        </div>
        <div style={{
          padding: '5px', borderRadius: '8px',
          color: isSelected ? meta.iconColor : '#cbd5e1',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Info size={14} />
        </div>
      </div>

      {/* Label */}
      <div style={{
        fontSize: '11px', fontWeight: 700, color: '#94a3b8',
        textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '6px',
      }}>
        {meta.label}
      </div>

      {/* Value + Unit (animated) */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginBottom: '6px' }}>
        <span style={{ fontSize: '32px', fontWeight: 900, color: '#1e293b', lineHeight: 1.1 }}>
          {typeof numericVal === 'number' ? <AnimatedNumber value={numericVal} decimals={1} /> : displayVal}
        </span>
        <span style={{ fontSize: '14px', fontWeight: 600, color: '#94a3b8' }}>{unit}</span>
      </div>

      {/* Status badge */}
      {status && (
        <div style={{ marginBottom: '8px' }}>
          <span style={{
            fontSize: '10px', fontWeight: 700, textTransform: 'uppercase',
            letterSpacing: '0.1em', padding: '3px 8px', borderRadius: '6px',
            background: meta.iconBg, color: meta.iconColor,
          }}>
            {status}
          </span>
        </div>
      )}

      {/* Small sparkline at bottom */}
      <div style={{
        position: 'absolute', bottom: 0, left: 0, right: 0, height: '45px',
        opacity: 0.5, pointerEvents: 'none',
      }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={history}>
            <defs>
              <linearGradient id={`grad-${sensorKey}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={meta.sparkColor} stopOpacity={0.3} />
                <stop offset="100%" stopColor={meta.sparkColor} stopOpacity={0} />
              </linearGradient>
            </defs>
            <Area
              type="monotone" dataKey={sensorKey}
              stroke={meta.sparkColor} fill={`url(#grad-${sensorKey})`}
              strokeWidth={2}
              isAnimationActive={true}
              animationDuration={600}
              animationEasing="ease-out"
            />
            <YAxis domain={['auto', 'auto']} hide />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

/* ═══════════════════════════════════════════════════
   MAIN APPLICATION
   ═══════════════════════════════════════════════════ */

export default function App() {
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)
  const [lastFetch, setLastFetch] = useState(null)
  const [history, setHistory] = useState([])
  const [scenarios, setScenarios] = useState([])
  const [manualScenarioId, setManualScenarioId] = useState(null)
  const [analysis, setAnalysis] = useState({ summary: '', flags: [] })
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [analysisError, setAnalysisError] = useState(null)

  const [activeSensorKey, setActiveSensorKey] = useState('voc_ppb')
  const [isTechOpen, setIsTechOpen] = useState(false)
  const [unitSystem, setUnitSystem] = useState('imperial')
  const [selectedActivity, setSelectedActivity] = useState('health')
  const [isScannerOpen, setIsScannerOpen] = useState(false)
  const [isPairingOpen, setIsPairingOpen] = useState(false)


  /* ── Data Fetching ── */

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/current-status`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setStatus(data)
      if (data.reading) {
        setHistory(prev => {
          const entry = {
            ...data.reading,
            timestamp: data.reading.timestamp_ms || Date.now(),
            health: data.score, sleep: data.sleep_score,
            study: data.study_score, work: data.work_score, fun: data.fun_score,
          }
          return [...prev, entry].slice(-30)
        })
      }
      setError(null)
      setLastFetch(new Date())
    } catch (err) {
      setError(`Unable to reach backend: ${err.message}`)
    }
  }, [])

  const fetchScenarios = useCallback(async () => {
    try {
      console.log(`📡 Fetching scenarios from: ${API_BASE}/api/scenarios`)
      const res = await fetch(`${API_BASE}/api/scenarios`)
      if (res.ok) {
        const data = await res.json()
        console.log(`✅ Loaded ${data.length} simulations.`)
        setScenarios(data)
      } else {
        console.warn(`⚠️ Scenarios fetch failed with status: ${res.status}`)
      }
    } catch (err) {
      console.error('❌ Failed to fetch scenarios:', err)
    }
  }, [])

  const selectScenario = async (id) => {
    try {
      setManualScenarioId(id)
      await fetch(`${API_BASE}/api/scenarios/select`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id }),
      })
      fetchStatus()
    } catch (err) { /* silently fail */ }
  }

  const fetchAnalysis = useCallback(async () => {
    setAnalysisLoading(true)
    setAnalysisError(null)
    try {
      const res = await fetch(`${API_BASE}/api/analyze`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setAnalysis(await res.json())
    } catch (err) {
      setAnalysisError(err.message)
    } finally {
      setAnalysisLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchStatus()
    fetchScenarios()
    const interval = setInterval(fetchStatus, POLL_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [fetchStatus, fetchScenarios])

  const reading = status?.reading ?? null
  const connected = status?.connected ?? false

  /* ═══════════════════════════════════════════════════
     RENDER
     ═══════════════════════════════════════════════════ */

  return (
    <div style={{
      minHeight: '100vh',
      background: '#f8fafc',
      fontFamily: "'Inter', system-ui, sans-serif",
      color: '#0f172a',
    }}>

      {/* ──────────── HEADER ──────────── */}
      <header style={{
        position: 'sticky', top: 0, zIndex: 40,
        background: 'rgba(255,255,255,0.85)', backdropFilter: 'blur(12px)',
        borderBottom: '1px solid #e2e8f0',
      }}>
        <div style={{
          maxWidth: '1600px', margin: '0 auto',
          padding: '0 24px', height: '64px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          {/* Left: Logo + Unit Toggle + Scan */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{
                background: '#4f46e5', padding: '8px', borderRadius: '12px',
                color: '#fff', display: 'flex',
              }}>
                <LayoutDashboard size={20} />
              </div>
              <span style={{ fontSize: '18px', fontWeight: 900, color: '#1e293b' }}>RoomPulse</span>
            </div>

            {/* Unit Toggle */}
            <div style={{
              display: 'flex', alignItems: 'center',
              background: '#f1f5f9', borderRadius: '12px',
              padding: '4px', border: '1px solid #e2e8f0',
            }}>
              {['metric', 'imperial'].map(sys => (
                <button
                  key={sys}
                  type="button"
                  onClick={() => setUnitSystem(sys)}
                  style={{
                    padding: '6px 16px', borderRadius: '8px', border: 'none', cursor: 'pointer',
                    fontSize: '12px', fontWeight: 700, textTransform: 'uppercase',
                    background: unitSystem === sys ? '#fff' : 'transparent',
                    color: unitSystem === sys ? '#4f46e5' : '#64748b',
                    boxShadow: unitSystem === sys ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {sys}
                </button>
              ))}
            </div>

            {/* Scan Room Button */}
            <button
              type="button"
              onClick={() => {
                const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
                if (isMobile) {
                  setIsScannerOpen(true);
                } else {
                  setIsPairingOpen(true);
                }
              }}
              style={{
                display: 'flex', alignItems: 'center', gap: '8px',
                padding: '8px 16px', borderRadius: '12px', border: '1px solid #e2e8f0',
                background: (isScannerOpen || isPairingOpen) ? '#f8fafc' : '#fff',
                color: (isScannerOpen || isPairingOpen) ? '#4f46e5' : '#64748b',
                fontSize: '12px', fontWeight: 700, cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              <Camera size={16} />
              <span style={{ whiteSpace: 'nowrap' }}>Scan Room</span>
            </button>
          </div>

          {/* Right: Source Selector + Settings */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            {/* Source dropdown */}
            <div style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              background: '#fff', border: '1px solid #e2e8f0',
              padding: '6px 14px', borderRadius: '12px',
            }}>
              <select
                value={manualScenarioId || 'live'}
                onChange={e => selectScenario(e.target.value)}
                style={{
                  background: 'transparent', border: 'none', outline: 'none',
                  fontSize: '12px', fontWeight: 700, color: '#334155', cursor: 'pointer',
                }}
              >
                <option value="live">📡 Live Hardware</option>
                <option value="weather">🌍 Local Weather</option>
                <optgroup label="Simulations">
                  {scenarios.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                </optgroup>
              </select>
              <div style={{
                width: '8px', height: '8px', borderRadius: '50%',
                background: connected ? '#10b981' : '#cbd5e1',
                boxShadow: connected ? '0 0 0 3px #d1fae5' : 'none',
              }} />
            </div>

            {/* Settings button */}
            <button
              type="button"
              onClick={() => setIsTechOpen(!isTechOpen)}
              style={{
                padding: '10px', borderRadius: '12px', border: 'none', cursor: 'pointer',
                background: 'transparent', color: '#64748b',
                transition: 'all 0.15s ease',
              }}
            >
              <Settings2 size={20} />
            </button>
          </div>
        </div>
      </header>

      {/* ──────────── MAIN CONTENT ──────────── */}
      <main style={{ maxWidth: '1600px', margin: '0 auto', padding: '32px 24px' }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr',
          gap: '32px',
        }}>
          {/* Responsive 8/4 grid via media query workaround: use CSS grid on large */}
          <style>{`
            @media (min-width: 1024px) {
              .rp-grid { grid-template-columns: 2fr 1fr !important; }
            }
          `}</style>
          <div className="rp-grid" style={{
            display: 'grid',
            gridTemplateColumns: '1fr',
            gap: '32px',
          }}>

            {/* ═══ LEFT COLUMN: Main Content ═══ */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>

              {/* ── Environment Scoring Gauges ── */}
              <div style={{
                background: '#f1f5f9', borderRadius: '24px',
                padding: '24px', border: '1px solid #e2e8f0',
              }}>
                <div style={{
                  fontSize: '11px', fontWeight: 800, textTransform: 'uppercase',
                  letterSpacing: '0.15em', color: '#94a3b8',
                  marginBottom: '16px', paddingLeft: '8px',
                }}>
                  Environment Scoring
                </div>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                  gap: '8px',
                }}>
                  {Object.entries(ACTIVITY_META).map(([key, meta]) => (
                    <SemiGauge
                      key={key}
                      label={meta.label}
                      sub={meta.sub}
                      color={meta.color}
                      value={status?.[key === 'health' ? 'score' : `${key}_score`] ?? 0}
                      activityKey={key}
                      isSelected={activeSensorKey === `activity_${key}`}
                      onSelect={setActiveSensorKey}
                    />
                  ))}
                </div>
              </div>

              {/* ── Live Telemetry Section ── */}
              <section>
                <div style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  marginBottom: '16px', padding: '0 4px',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{
                      background: '#d1fae5', color: '#059669',
                      padding: '6px', borderRadius: '8px', display: 'flex',
                    }}>
                      <Zap size={14} />
                    </div>
                    <h2 style={{
                      fontSize: '12px', fontWeight: 800, textTransform: 'uppercase',
                      letterSpacing: '0.15em', color: '#64748b', margin: 0,
                    }}>
                      Live Telemetry
                    </h2>
                  </div>
                  {lastFetch && (
                    <span style={{
                      fontSize: '10px', fontWeight: 700, color: '#94a3b8',
                      textTransform: 'uppercase', letterSpacing: '0.1em',
                    }}>
                      Updated: {lastFetch.toLocaleTimeString()}
                    </span>
                  )}
                </div>

                {/* Sensor cards grid */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
                  gap: '16px',
                }}>
                  {Object.keys(SENSOR_META).map(key => (
                    <StatusCard
                      key={key}
                      sensorKey={key}
                      value={reading?.[key]}
                      history={history}
                      unitSystem={unitSystem}
                      onSelect={setActiveSensorKey}
                      isSelected={activeSensorKey === key}
                    />
                  ))}
                </div>
              </section>
            </div>

            {/* ═══ RIGHT COLUMN: Sidebar ═══ */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>

              {/* ── AI Room Analysis ── */}
              <div style={{
                background: '#fff', border: '1px solid #e2e8f0',
                borderRadius: '20px', padding: '24px',
                boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
              }}>
                {/* Panel header */}
                <div style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  marginBottom: '24px',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{
                      background: '#eef2ff', color: '#4f46e5',
                      padding: '10px', borderRadius: '14px',
                      border: '1px solid #e0e7ff', display: 'flex',
                    }}>
                      <BrainCircuit size={22} />
                    </div>
                    <div>
                      <h3 style={{ fontSize: '15px', fontWeight: 800, color: '#1e293b', margin: 0 }}>
                        Room Analysis
                      </h3>
                      <p style={{
                        fontSize: '10px', fontWeight: 700, color: '#94a3b8',
                        textTransform: 'uppercase', letterSpacing: '0.15em', margin: 0,
                      }}>
                        Neural Insight
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={fetchAnalysis}
                    disabled={analysisLoading}
                    style={{
                      padding: '8px', borderRadius: '10px', border: 'none', cursor: 'pointer',
                      background: 'transparent', color: '#94a3b8',
                      opacity: analysisLoading ? 0.5 : 1,
                    }}
                  >
                    <RefreshCw size={18} className={analysisLoading ? 'animate-spin' : ''} />
                  </button>
                </div>

                {/* Analysis content */}
                <div style={{ minHeight: '200px' }}>
                  {analysisLoading ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      {[100, 90, 75].map((w, i) => (
                        <div key={i} style={{
                          height: '16px', borderRadius: '8px', background: '#f1f5f9',
                          width: `${w}%`,
                        }} />
                      ))}
                    </div>
                  ) : analysisError ? (
                    <div style={{
                      display: 'flex', flexDirection: 'column', alignItems: 'center',
                      justifyContent: 'center', padding: '24px',
                      background: '#fff1f2', borderRadius: '16px', border: '1px solid #fecdd3',
                    }}>
                      <AlertCircle size={24} color="#f43f5e" style={{ marginBottom: '8px' }} />
                      <p style={{ fontSize: '12px', fontWeight: 700, color: '#e11d48', margin: 0 }}>
                        {analysisError}
                      </p>
                    </div>
                  ) : !analysis.summary ? (
                    <div style={{
                      display: 'flex', flexDirection: 'column', alignItems: 'center',
                      justifyContent: 'center', textAlign: 'center', padding: '32px 16px',
                    }}>
                      <div style={{
                        width: '64px', height: '64px', borderRadius: '50%',
                        background: '#f1f5f9', display: 'flex', alignItems: 'center',
                        justifyContent: 'center', marginBottom: '16px', color: '#cbd5e1',
                      }}>
                        <BrainCircuit size={32} />
                      </div>
                      <h4 style={{ fontSize: '14px', fontWeight: 700, color: '#1e293b', margin: '0 0 4px 0' }}>
                        No Active Insight
                      </h4>
                      <p style={{ fontSize: '12px', color: '#94a3b8', maxWidth: '200px', margin: '0 0 20px 0', lineHeight: 1.5 }}>
                        Run analysis to get an AI-powered breakdown of your environment.
                      </p>
                      <button
                        type="button"
                        onClick={fetchAnalysis}
                        style={{
                          display: 'flex', alignItems: 'center', gap: '8px',
                          background: '#4f46e5', color: '#fff',
                          padding: '10px 20px', borderRadius: '14px', border: 'none',
                          fontSize: '12px', fontWeight: 700, cursor: 'pointer',
                          boxShadow: '0 4px 12px rgba(79,70,229,0.3)',
                        }}
                      >
                        Start Analysis
                      </button>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                      <p style={{
                        fontSize: '14px', color: '#475569', lineHeight: 1.7,
                        fontStyle: 'italic', margin: 0,
                      }}>
                        "{analysis.summary}"
                      </p>
                      {analysis.flags?.length > 0 && (
                        <div>
                          <p style={{
                            fontSize: '10px', fontWeight: 800, textTransform: 'uppercase',
                            letterSpacing: '0.15em', color: '#94a3b8', margin: '0 0 8px 0',
                          }}>
                            Attention Areas
                          </p>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            {analysis.flags.map((flag, i) => (
                              <div key={i} style={{
                                display: 'flex', alignItems: 'flex-start', gap: '8px',
                                background: '#f8fafc', padding: '10px 12px',
                                borderRadius: '12px', border: '1px solid #f1f5f9',
                              }}>
                                <CheckCircle2 size={14} color="#4f46e5" style={{ marginTop: '2px', flexShrink: 0 }} />
                                <span style={{ fontSize: '12px', fontWeight: 500, color: '#475569' }}>
                                  {flag}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Footer */}
                <div style={{
                  marginTop: '24px', paddingTop: '16px', borderTop: '1px solid #f1f5f9',
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  fontSize: '10px', fontWeight: 700, letterSpacing: '0.15em',
                  textTransform: 'uppercase', color: '#94a3b8',
                }}>
                  <span>ENGINE: GEMINI 2.0</span>
                  <span style={{ color: '#4f46e5' }}>ACTIVE</span>
                </div>
              </div>

              {/* ── Dynamic Sensor Reference Panel ── */}
              {(() => {
                const rawKey = activeSensorKey || 'voc_ppb'
                const isActivity = rawKey.startsWith('activity_')
                const lookupKey = isActivity ? rawKey.replace('activity_', '') : rawKey
                const refMeta = isActivity ? ACTIVITY_META[lookupKey] : SENSOR_META[rawKey]
                if (!refMeta) return null
                const RefIcon = refMeta.icon
                const currentValue = isActivity
                  ? (status?.[lookupKey === 'health' ? 'score' : `${lookupKey}_score`] ?? null)
                  : (reading?.[rawKey] ?? null)
                return (
                  <div style={{
                    background: '#fff', border: '1px solid #e2e8f0',
                    borderRadius: '20px', padding: '24px',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
                    transition: 'all 0.2s ease',
                  }}>
                    <div style={{
                      display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px',
                    }}>
                      <div style={{
                        background: refMeta.iconBg, color: refMeta.iconColor,
                        padding: '10px', borderRadius: '14px',
                        border: `1px solid ${refMeta.iconBorder}`, display: 'flex',
                      }}>
                        <RefIcon size={22} />
                      </div>
                      <div>
                        <h3 style={{ fontSize: '15px', fontWeight: 800, color: '#1e293b', margin: 0 }}>
                          {refMeta.label} Reference
                        </h3>
                        <p style={{
                          fontSize: '10px', fontWeight: 700, color: '#94a3b8',
                          textTransform: 'uppercase', letterSpacing: '0.15em', margin: 0,
                        }}>
                          Thresholds
                        </p>
                      </div>
                    </div>

                    {/* Current value highlight */}
                    {currentValue != null && (
                      <div style={{
                        display: 'flex', alignItems: 'baseline', gap: '8px',
                        marginBottom: '20px', padding: '14px 16px',
                        background: refMeta.iconBg, borderRadius: '14px',
                        border: `1px solid ${refMeta.iconBorder}`,
                      }}>
                        <span style={{ fontSize: '28px', fontWeight: 900, color: '#1e293b' }}>
                          {(() => {
                            if (isActivity) return Math.round(currentValue)
                            const conv = CONVERSIONS[rawKey]?.[unitSystem]
                            const v = conv ? conv.convert(currentValue) : currentValue
                            return typeof v === 'number' ? <AnimatedNumber value={v} decimals={1} /> : v
                          })()}
                        </span>
                        <span style={{ fontSize: '14px', fontWeight: 600, color: '#64748b' }}>
                          {isActivity ? 'pts' : (CONVERSIONS[rawKey]?.[unitSystem]?.unit || refMeta.unit)}
                        </span>
                        <span style={{
                          marginLeft: 'auto', fontSize: '11px', fontWeight: 700,
                          color: refMeta.iconColor, textTransform: 'uppercase',
                        }}>
                          {refMeta.getStatus(currentValue)}
                        </span>
                      </div>
                    )}

                    {/* Trend Chart */}
                    {!isActivity && history.length > 1 && (() => {
                      const chartUnit = CONVERSIONS[rawKey]?.[unitSystem]?.unit || refMeta.unit
                      const chartData = history.map((entry, i) => {
                        const raw = entry[rawKey]
                        const conv = CONVERSIONS[rawKey]?.[unitSystem]
                        const v = conv && raw != null ? conv.convert(raw) : raw
                        return { index: i, value: v != null ? parseFloat(v.toFixed(1)) : null }
                      })
                      return (
                        <div style={{
                          height: '160px', marginBottom: '20px',
                          background: '#f8fafc', borderRadius: '14px',
                          padding: '14px 8px 8px 0', border: '1px solid #f1f5f9',
                        }}>
                          <div style={{
                            fontSize: '10px', fontWeight: 800, textTransform: 'uppercase',
                            letterSpacing: '0.15em', color: '#94a3b8',
                            marginBottom: '8px', paddingLeft: '16px',
                          }}>
                            {refMeta.label} Trend — Last {chartData.length} Readings
                          </div>
                          <ResponsiveContainer width="100%" height="85%">
                            <AreaChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                              <defs>
                                <linearGradient id={`grad-sidebar-${rawKey}`} x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="0%" stopColor={refMeta.sparkColor || refMeta.iconColor} stopOpacity={0.2} />
                                  <stop offset="100%" stopColor={refMeta.sparkColor || refMeta.iconColor} stopOpacity={0.02} />
                                </linearGradient>
                              </defs>
                              <XAxis
                                dataKey="index" hide={false}
                                tick={{ fontSize: 9, fill: '#94a3b8' }}
                                axisLine={{ stroke: '#e2e8f0' }}
                                tickLine={false}
                                tickFormatter={(i) => `${i + 1}`}
                                interval={Math.max(0, Math.floor(chartData.length / 5) - 1)}
                              />
                              <YAxis
                                domain={['auto', 'auto']}
                                tick={{ fontSize: 9, fill: '#94a3b8' }}
                                axisLine={false}
                                tickLine={false}
                                width={40}
                                tickFormatter={(v) => `${v}`}
                              />
                              <Tooltip
                                contentStyle={{
                                  background: '#0f172a', border: 'none', borderRadius: '10px',
                                  padding: '6px 10px', fontSize: '11px', color: '#fff', fontWeight: 700,
                                }}
                                labelFormatter={() => ''}
                                formatter={(v) => [`${v} ${chartUnit}`, refMeta.label]}
                              />
                              <Area
                                type="monotone" dataKey="value"
                                stroke={refMeta.sparkColor || refMeta.iconColor}
                                fill={`url(#grad-sidebar-${rawKey})`}
                                strokeWidth={2}
                                isAnimationActive={true}
                                animationDuration={600}
                                animationEasing="ease-out"
                                dot={false}
                                activeDot={{ r: 3, fill: refMeta.sparkColor || refMeta.iconColor, strokeWidth: 0 }}
                              />
                            </AreaChart>
                          </ResponsiveContainer>
                        </div>
                      )
                    })()}

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                      {refMeta.ranges.map((range, i) => {
                        const isActiveRange = currentValue != null && (() => {
                          const v = currentValue
                          const prevMax = i > 0 ? refMeta.ranges[i - 1].max : -Infinity
                          return v > prevMax && v <= range.max
                        })()
                        return (
                          <div key={i} style={{
                            padding: isActiveRange ? '10px 12px' : '0',
                            borderRadius: '12px',
                            background: isActiveRange ? refMeta.iconBg : 'transparent',
                            border: isActiveRange ? `1px solid ${refMeta.iconBorder}` : '1px solid transparent',
                            transition: 'all 0.2s ease',
                          }}>
                            <div style={{
                              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                              marginBottom: '6px',
                            }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <div style={{
                                  width: '8px', height: '8px', borderRadius: '50%', background: range.color,
                                }} />
                                <span style={{
                                  fontSize: '12px', fontWeight: isActiveRange ? 800 : 700,
                                  color: isActiveRange ? '#0f172a' : '#334155',
                                }}>
                                  {range.label}
                                </span>
                              </div>
                              <span style={{ fontSize: '11px', fontWeight: 800, color: '#94a3b8' }}>
                                {range.max} {refMeta.unit}
                              </span>
                            </div>
                            <div style={{
                              height: '6px', width: '100%', background: '#f8fafc',
                              borderRadius: '99px', overflow: 'hidden', marginBottom: '4px',
                            }}>
                              <div style={{
                                height: '100%', background: range.color,
                                opacity: isActiveRange ? 0.6 : 0.2,
                                width: '100%', borderRadius: '99px',
                                transition: 'opacity 0.2s ease',
                              }} />
                            </div>
                            <p style={{
                              fontSize: '11px', color: isActiveRange ? '#475569' : '#94a3b8',
                              lineHeight: 1.4, margin: 0,
                            }}>
                              {range.text}
                            </p>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )
              })()}
            </div> {/* End Right Column */}
          </div> {/* End rp-grid */}
        </div> {/* End Outer grid */}
      </main>

      {/* Modal removed — info now updates the sidebar reference panel */}

      {/* ──────────── SETTINGS DRAWER ──────────── */}
      {isTechOpen && (
        <>
          {/* Backdrop */}
          <div
            onClick={() => setIsTechOpen(false)}
            style={{
              position: 'fixed', inset: 0, zIndex: 40,
              background: 'rgba(15,23,42,0.2)', backdropFilter: 'blur(4px)',
            }}
          />
          {/* Drawer */}
          <aside style={{
            position: 'fixed', top: 0, left: 0, bottom: 0, zIndex: 50,
            width: '100%', maxWidth: '380px',
            background: '#fff', borderRight: '1px solid #e2e8f0',
            boxShadow: '4px 0 24px rgba(0,0,0,0.1)',
            padding: '32px', display: 'flex', flexDirection: 'column',
            animation: 'slideIn 0.2s ease-out',
            overflowY: 'auto',
          }}>
            {/* Drawer header */}
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              marginBottom: '32px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  background: '#4f46e5', padding: '8px', borderRadius: '12px',
                  color: '#fff', display: 'flex',
                }}>
                  <BrainCircuit size={20} />
                </div>
                <h3 style={{ fontSize: '18px', fontWeight: 900, color: '#1e293b', margin: 0 }}>
                  Neural Engine
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setIsTechOpen(false)}
                style={{
                  padding: '8px', border: 'none', cursor: 'pointer',
                  background: 'transparent', color: '#cbd5e1',
                }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Scenarios */}
            <div style={{ marginBottom: '32px' }}>
              <h4 style={{
                fontSize: '10px', fontWeight: 800, textTransform: 'uppercase',
                letterSpacing: '0.2em', color: '#94a3b8', marginBottom: '16px',
              }}>
                Neural Override
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {/* Live feed option */}
                <button
                  type="button"
                  onClick={() => selectScenario('live')}
                  style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '14px 16px', borderRadius: '14px', cursor: 'pointer',
                    border: '1px solid ' + (!manualScenarioId || manualScenarioId === 'live' ? '#c7d2fe' : '#e2e8f0'),
                    background: !manualScenarioId || manualScenarioId === 'live' ? '#eef2ff' : '#fff',
                    color: !manualScenarioId || manualScenarioId === 'live' ? '#4f46e5' : '#64748b',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <LayoutDashboard size={18} />
                    <span style={{ fontSize: '12px', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                      Live Feed
                    </span>
                  </div>
                  <ChevronRight size={16} />
                </button>
                {/* Scenario list */}
                {scenarios.map(s => (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => selectScenario(s.id)}
                    style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                      padding: '14px 16px', borderRadius: '14px', cursor: 'pointer',
                      border: '1px solid ' + (manualScenarioId === s.id ? '#c7d2fe' : '#e2e8f0'),
                      background: manualScenarioId === s.id ? '#eef2ff' : '#fff',
                      color: manualScenarioId === s.id ? '#4f46e5' : '#64748b',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{ fontSize: '16px' }}>{s.icon}</span>
                      <span style={{ fontSize: '12px', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                        {s.name}
                      </span>
                    </div>
                    <ChevronRight size={16} />
                  </button>
                ))}
              </div>
            </div>

            {/* Calculation log */}
            <div style={{ marginBottom: '32px' }}>
              <h4 style={{
                fontSize: '10px', fontWeight: 800, textTransform: 'uppercase',
                letterSpacing: '0.2em', color: '#94a3b8', marginBottom: '16px',
              }}>
                Calculation Log
              </h4>
              <div style={{
                background: '#f8fafc', padding: '20px', borderRadius: '16px',
                border: '1px solid #f1f5f9',
                fontFamily: 'monospace', fontSize: '11px', lineHeight: 1.8,
                color: '#64748b', maxHeight: '240px', overflowY: 'auto',
              }}>
                {status?.breakdown ? (
                  <div>
                    <div style={{ color: '#4f46e5', fontWeight: 700, marginBottom: '8px' }}>
                      // Health Algorithm (MLP)
                    </div>
                    <div>Base MLP Score: <strong style={{ color: '#334155' }}>{status.breakdown.base_mlp_score?.toFixed(1) || '0.0'}</strong></div>
                    <div>VOC Penalty: <strong style={{ color: '#f43f5e' }}>{status.breakdown.voc_penalty?.toFixed(1) || '0.0'}</strong></div>
                    <div>PM2.5 Penalty: <strong style={{ color: '#f43f5e' }}>{status.breakdown.pm25_penalty?.toFixed(1) || '0.0'}</strong></div>
                    <div style={{ borderTop: '1px solid #e2e8f0', marginTop: '8px', paddingTop: '8px' }}>
                      Final IAQ: <strong style={{ color: '#0f172a', fontSize: '13px' }}>{status.breakdown.final_score || '0'}</strong>
                    </div>
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: '16px', color: '#cbd5e1' }}>
                    Waiting for data...
                  </div>
                )}
              </div>
            </div>

            {/* Footer */}
            <div style={{ marginTop: 'auto', paddingTop: '24px', borderTop: '1px solid #f1f5f9' }}>
              <div style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                fontSize: '10px', fontWeight: 800, color: '#cbd5e1',
                textTransform: 'uppercase', letterSpacing: '0.15em',
              }}>
                <span>Core v1.4.2</span>
                <span>RoomPulse System</span>
              </div>
            </div>
          </aside>
        </>
      )}

      {/* ──────────── ERROR BANNER ──────────── */}
      {error && (
        <div style={{
          position: 'fixed', bottom: '24px', left: '50%', transform: 'translateX(-50%)',
          zIndex: 50, maxWidth: '420px', width: '100%', padding: '0 24px',
        }}>
          <div style={{
            background: '#e11d48', color: '#fff',
            padding: '14px 20px', borderRadius: '16px',
            display: 'flex', alignItems: 'center', gap: '12px',
            boxShadow: '0 8px 24px rgba(225,29,72,0.3)',
          }}>
            <AlertCircle size={18} />
            <p style={{ fontSize: '12px', fontWeight: 700, margin: 0 }}>{error}</p>
          </div>
        </div>
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

