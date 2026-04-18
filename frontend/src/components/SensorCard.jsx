import React from 'react'
import './SensorCard.css'

/* ─────────────────────────────────────────
   SVG Icons — clean line-art
   ───────────────────────────────────────── */

const Icons = {
  temperature: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0Z" />
    </svg>
  ),
  humidity: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0L12 2.69Z" />
    </svg>
  ),
  light: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="5" />
      <line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" />
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
      <line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" />
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
    </svg>
  ),
  noise: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
      <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
    </svg>
  ),
  pressure: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <path d="M12 6v6l4 2" />
    </svg>
  ),
  particles: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="7" cy="10" r="2" /><circle cx="17" cy="8" r="2.5" />
      <circle cx="12" cy="17" r="1.5" /><circle cx="5" cy="18" r="1" />
      <circle cx="19" cy="16" r="1.5" />
    </svg>
  ),
  voc: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 22V11a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v11" />
      <path d="M6 10V6.5C6 4.01 8.01 2 10.5 2h3C15.99 2 18 4.01 18 6.5V10" />
      <line x1="6" y1="22" x2="18" y2="22" />
    </svg>
  ),
}

/* ─────────────────────────────────────────
   Sensor configs with status words + colors
   ───────────────────────────────────────── */

const SENSOR_META = {
  temperature_c: {
    label: 'Temperature', unit: '°C', icon: 'temperature',
    min: 10, max: 40,
    palette: { bg: 'var(--temp-bg)', accent: 'var(--temp-accent)', iconBg: 'var(--temp-icon)' },
    getStatus: v => v < 18 ? 'Cold' : v < 20 ? 'Cool' : v <= 24 ? 'Ideal' : v <= 28 ? 'Warm' : 'Hot',
  },
  humidity_pct: {
    label: 'Humidity', unit: '%', icon: 'humidity',
    min: 0, max: 100,
    palette: { bg: 'var(--humid-bg)', accent: 'var(--humid-accent)', iconBg: 'var(--humid-icon)' },
    getStatus: v => v < 30 ? 'Dry' : v < 40 ? 'Low' : v <= 60 ? 'Balanced' : v <= 70 ? 'Humid' : 'Damp',
  },
  light_lux: {
    label: 'Light', unit: 'lux', icon: 'light',
    min: 0, max: 1000,
    palette: { bg: 'var(--light-bg)', accent: 'var(--light-accent)', iconBg: 'var(--light-icon)' },
    getStatus: v => v < 100 ? 'Dim' : v < 300 ? 'Low' : v <= 500 ? 'Optimal' : v <= 800 ? 'Bright' : 'Intense',
  },
  noise_db: {
    label: 'Noise', unit: 'dB', icon: 'noise',
    min: 0, max: 100,
    palette: { bg: 'var(--noise-bg)', accent: 'var(--noise-accent)', iconBg: 'var(--noise-icon)' },
    getStatus: v => v < 30 ? 'Silent' : v < 45 ? 'Quiet' : v <= 55 ? 'Moderate' : v <= 70 ? 'Loud' : 'Noisy',
  },
  pressure_hpa: {
    label: 'Pressure', unit: 'hPa', icon: 'pressure',
    min: 960, max: 1060,
    palette: { bg: 'var(--press-bg)', accent: 'var(--press-accent)', iconBg: 'var(--press-icon)' },
    getStatus: v => v < 1000 ? 'Low' : v <= 1025 ? 'Normal' : 'High',
  },
  pm25_ugm3: {
    label: 'PM 2.5', unit: 'µg/m³', icon: 'particles',
    min: 0, max: 150,
    palette: { bg: 'var(--pm-bg)', accent: 'var(--pm-accent)', iconBg: 'var(--pm-icon)' },
    getStatus: v => v < 12 ? 'Clean' : v < 35 ? 'Moderate' : v < 55 ? 'Unhealthy' : 'Poor',
  },
  voc_ppb: {
    label: 'VOC', unit: 'ppb', icon: 'voc',
    min: 0, max: 1500,
    palette: { bg: 'var(--voc-bg)', accent: 'var(--voc-accent)', iconBg: 'var(--voc-icon)' },
    getStatus: v => v < 300 ? 'Fresh' : v < 500 ? 'Acceptable' : v < 1000 ? 'Elevated' : 'Poor',
  },
}

/* ─────────────────────────────────────────
   SensorCard
   ───────────────────────────────────────── */

function SensorCard({ sensorKey, value }) {
  const meta = SENSOR_META[sensorKey]
  if (!meta) return null

  const isLoading = value === null || value === undefined
  const displayVal = isLoading ? '—' : typeof value === 'number' ? value.toFixed(1) : value
  const statusWord = isLoading ? '' : meta.getStatus(value)

  const barPercent = isLoading
    ? 0
    : Math.max(0, Math.min(100, ((value - meta.min) / (meta.max - meta.min)) * 100))

  return (
    <div
      className={`env-card ${isLoading ? 'env-card--loading' : ''}`}
      style={{ '--card-bg': meta.palette.bg, '--card-accent': meta.palette.accent, '--card-icon-bg': meta.palette.iconBg }}
      id={`sensor-${sensorKey}`}
    >
      <div className="env-card__icon-wrap">
        {Icons[meta.icon]}
      </div>

      <div className="env-card__info">
        <span className="env-card__label">{meta.label}</span>
        {statusWord && <span className="env-card__status">{statusWord}</span>}
      </div>

      <div className="env-card__data">
        <span className="env-card__value">{displayVal}</span>
        {!isLoading && <span className="env-card__unit">{meta.unit}</span>}
      </div>

      <div className="env-card__bar">
        <div className="env-card__bar-fill" style={{ width: `${barPercent}%` }} />
      </div>
    </div>
  )
}

/* ─────────────────────────────────────────
   SensorGrid
   ───────────────────────────────────────── */

export default function SensorGrid({ reading }) {
  const keys = Object.keys(SENSOR_META)
  return (
    <div className="env-grid">
      {keys.map(key => (
        <SensorCard key={key} sensorKey={key} value={reading ? reading[key] : null} />
      ))}
    </div>
  )
}

export { SensorCard, SENSOR_META }
