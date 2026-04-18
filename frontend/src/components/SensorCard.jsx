import React, { useState } from 'react'
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
  info: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <path d="M12 16v-4" />
      <path d="M12 8h.01" />
    </svg>
  ),
  close: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 6 6 18" />
      <path d="m6 6 12 12" />
    </svg>
  ),
}

/* ─────────────────────────────────────────
   Sensor configs with status words + colors
   ───────────────────────────────────────── */

const SENSOR_META = {
  temperature_c: {
    label: 'Temperature', unit: '°C', icon: 'temperature',
    description: 'Measures the thermal intensity of the space. Comfort usually peaks between 20°C and 24°C.',
    min: 10, max: 40,
    palette: { bg: 'var(--temp-bg)', accent: 'var(--temp-accent)', iconBg: 'var(--temp-icon)' },
    getStatus: v => v < 18 ? 'Cold' : v < 20 ? 'Cool' : v <= 24 ? 'Ideal' : v <= 28 ? 'Warm' : 'Hot',
    ranges: [
      { label: 'Cold', max: 18, color: '#4a8fe7' },
      { label: 'Cool', min: 18, max: 20, color: '#7baefa' },
      { label: 'Ideal', min: 20, max: 24, color: '#4aab7a' },
      { label: 'Warm', min: 24, max: 28, color: '#d9a74a' },
      { label: 'Hot', min: 28, color: '#d96a5c' },
    ]
  },
  humidity_pct: {
    label: 'Humidity', unit: '%', icon: 'humidity',
    description: 'The amount of water vapor in the air. Balanced levels prevent mold and dry skin.',
    min: 0, max: 100,
    palette: { bg: 'var(--humid-bg)', accent: 'var(--humid-accent)', iconBg: 'var(--humid-icon)' },
    getStatus: v => v < 30 ? 'Dry' : v < 40 ? 'Low' : v <= 60 ? 'Balanced' : v <= 70 ? 'Humid' : 'Damp',
    ranges: [
      { label: 'Dry', max: 30, color: '#d9a74a' },
      { label: 'Low', min: 30, max: 40, color: '#7baefa' },
      { label: 'Balanced', min: 40, max: 60, color: '#4aab7a' },
      { label: 'Humid', min: 60, max: 70, color: '#4a8fe7' },
      { label: 'Damp', min: 70, color: '#3272d9' },
    ]
  },
  light_lux: {
    label: 'Light', unit: 'lux', icon: 'light',
    description: 'Ambient brightness level. Higher values promote alertness; lower values suit relaxation.',
    min: 0, max: 1000,
    palette: { bg: 'var(--light-bg)', accent: 'var(--light-accent)', iconBg: 'var(--light-icon)' },
    getStatus: v => v < 100 ? 'Dim' : v < 300 ? 'Low' : v <= 500 ? 'Optimal' : v <= 800 ? 'Bright' : 'Intense',
    ranges: [
      { label: 'Dim', max: 100, color: '#9a948c' },
      { label: 'Low', min: 100, max: 300, color: '#c9b16e' },
      { label: 'Optimal', min: 300, max: 500, color: '#4aab7a' },
      { label: 'Bright', min: 500, max: 800, color: '#d4a017' },
      { label: 'Intense', min: 800, color: '#e66b4d' },
    ]
  },
  noise_db: {
    label: 'Noise', unit: 'dB', icon: 'noise',
    description: 'Measures sound pressure. Sustained levels above 70dB can be distruptive.',
    min: 0, max: 100,
    palette: { bg: 'var(--noise-bg)', accent: 'var(--noise-accent)', iconBg: 'var(--noise-icon)' },
    getStatus: v => v < 30 ? 'Silent' : v < 45 ? 'Quiet' : v <= 55 ? 'Moderate' : v <= 70 ? 'Loud' : 'Noisy',
    ranges: [
      { label: 'Silent', max: 30, color: '#4aab7a' },
      { label: 'Quiet', min: 30, max: 45, color: '#7baefa' },
      { label: 'Moderate', min: 45, max: 55, color: '#d9a74a' },
      { label: 'Loud', min: 55, max: 70, color: '#e66b4d' },
      { label: 'Noisy', min: 70, color: '#d96a5c' },
    ]
  },
  pressure_hpa: {
    label: 'Pressure', unit: 'hPa', icon: 'pressure',
    description: 'Atmospheric pressure. Changes often correlate with shifts in local weather patterns.',
    min: 960, max: 1060,
    palette: { bg: 'var(--press-bg)', accent: 'var(--press-accent)', iconBg: 'var(--press-icon)' },
    getStatus: v => v < 1000 ? 'Low' : v <= 1025 ? 'Normal' : 'High',
    ranges: [
      { label: 'Low', max: 1000, color: '#7baefa' },
      { label: 'Normal', min: 1000, max: 1025, color: '#4aab7a' },
      { label: 'High', min: 1025, color: '#d9a74a' },
    ]
  },
  pm25_ugm3: {
    label: 'PM 2.5', unit: 'µg/m³', icon: 'particles',
    description: 'Fine particulate matter. Lower concentration ensures healthier indoor air quality.',
    min: 0, max: 150,
    palette: { bg: 'var(--pm-bg)', accent: 'var(--pm-accent)', iconBg: 'var(--pm-icon)' },
    getStatus: v => v < 12 ? 'Clean' : v < 35 ? 'Moderate' : v < 55 ? 'Unhealthy' : 'Poor',
    ranges: [
      { label: 'Clean', max: 12, color: '#4aab7a' },
      { label: 'Moderate', min: 12, max: 35, color: '#d9a74a' },
      { label: 'Unhealthy', min: 35, max: 55, color: '#e66b4d' },
      { label: 'Poor', min: 55, color: '#d96a5c' },
    ]
  },
  voc_ppb: {
    label: 'VOC', unit: 'ppb', icon: 'voc',
    description: 'Volatile Organic Compounds. Elevated levels may indicate poor ventilation or chemicals.',
    min: 0, max: 1500,
    palette: { bg: 'var(--voc-bg)', accent: 'var(--voc-accent)', iconBg: 'var(--voc-icon)' },
    getStatus: v => v < 300 ? 'Fresh' : v < 500 ? 'Acceptable' : v < 1000 ? 'Elevated' : 'Poor',
    ranges: [
      { label: 'Fresh', max: 300, color: '#4aab7a' },
      { label: 'Acceptable', min: 300, max: 500, color: '#7baefa' },
      { label: 'Elevated', min: 500, max: 1000, color: '#d9a74a' },
      { label: 'Poor', min: 1000, color: '#d96a5c' },
    ]
  },
}

/* ─────────────────────────────────────────
   Modal Component
   ───────────────────────────────────────── */

function SensorInfoModal({ meta, value, onClose }) {
  if (!meta) return null

  const displayVal = (value === null || value === undefined) ? '—' : typeof value === 'number' ? value.toFixed(1) : value
  const statusWord = (value === null || value === undefined) ? 'Unknown' : meta.getStatus(value)

  return (
    <div className="env-modal-backdrop" onClick={onClose}>
      <div className="env-modal" onClick={e => e.stopPropagation()}>
        <button className="env-modal__close" onClick={onClose}>
          {Icons.close}
        </button>

        <div className="env-modal__header">
          <div className="env-modal__icon" style={{ background: meta.palette.iconBg, color: meta.palette.accent }}>
            {Icons[meta.icon]}
          </div>
          <div>
            <h3>{meta.label} Analysis</h3>
            <p className="env-modal__subtitle">Currently sitting at <span style={{ color: meta.palette.accent, fontWeight: 700 }}>{displayVal}{meta.unit}</span> ({statusWord})</p>
          </div>
        </div>

        <div className="env-modal__body">
          <p className="env-modal__desc">{meta.description}</p>
          
          <div className="env-modal__ranges">
            <h4 className="env-modal__section-title">Reference Ranges</h4>
            {meta.ranges.map((r, i) => (
              <div key={i} className="env-modal__range-item">
                <div className="env-modal__range-color" style={{ background: r.color }} />
                <span className="env-modal__range-label">{r.label}</span>
                <span className="env-modal__range-val">
                  {r.min !== undefined && r.max !== undefined ? `${r.min} - ${r.max}` : 
                   r.min !== undefined ? `> ${r.min}` : 
                   `< ${r.max}`} {meta.unit}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

/* ─────────────────────────────────────────
   SensorCard
   ───────────────────────────────────────── */

function SensorCard({ sensorKey, value }) {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const meta = SENSOR_META[sensorKey]
  if (!meta) return null

  const isLoading = value === null || value === undefined
  const displayVal = isLoading ? '—' : typeof value === 'number' ? value.toFixed(1) : value
  const statusWord = isLoading ? '' : meta.getStatus(value)

  const barPercent = isLoading
    ? 0
    : Math.max(0, Math.min(100, ((value - meta.min) / (meta.max - meta.min)) * 100))

  return (
    <>
      <div
        className={`env-card ${isLoading ? 'env-card--loading' : ''}`}
        style={{ '--card-bg': meta.palette.bg, '--card-accent': meta.palette.accent, '--card-icon-bg': meta.palette.iconBg }}
        id={`sensor-${sensorKey}`}
      >
        <button 
          className="env-card__info-btn" 
          onClick={() => setIsModalOpen(true)}
          title={`More about ${meta.label}`}
        >
          {Icons.info}
        </button>

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

      {isModalOpen && (
        <SensorInfoModal 
          meta={meta} 
          value={value} 
          onClose={() => setIsModalOpen(false)} 
        />
      )}
    </>
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
