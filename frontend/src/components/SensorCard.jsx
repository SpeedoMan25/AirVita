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
  health: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
    </svg>
  ),
  sleep: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
    </svg>
  ),
  study: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z" />
    </svg>
  ),
  work: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
      <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
    </svg>
  ),
  fun: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 3v1" /><path d="M12 20v1" />
      <path d="M3 12h1" /><path d="M20 12h1" />
      <path d="m18.364 5.636-.707.707" /><path d="m6.343 17.657-.707.707" />
      <path d="m5.636 5.636.707.707" /><path d="m17.657 17.657.707.707" />
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
  health: {
    label: 'Room Health', unit: '', icon: 'health',
    description: 'Overall environment balance. Combines IAQ (VOC/Particulates) with core comfort metrics (Temp/Humidity) via our Hybrid Neural Engine.',
    min: 0, max: 99,
    palette: { bg: '#f0f9f1', accent: '#4aab7a', iconBg: '#e2f2e7' },
    getStatus: v => v < 40 ? 'Poor' : v < 60 ? 'Fair' : v < 80 ? 'Good' : 'Excellent',
    ranges: [
      { label: 'Poor', max: 40, color: '#d96a5c' },
      { label: 'Fair', min: 40, max: 60, color: '#d9a74a' },
      { label: 'Good', min: 60, max: 80, color: '#4aab7a' },
      { label: 'Excellent', min: 80, color: '#2d6a4f' },
    ]
  },
  sleep: {
    label: 'Sleep Quality', unit: '', icon: 'sleep',
    description: 'Measures restorative potential. Prioritizes low light (< 10 lux), cool temperatures, and minimal noise for deep REM cycles.',
    min: 0, max: 99,
    palette: { bg: '#f1f0f9', accent: '#667eea', iconBg: '#e7e6f2' },
    getStatus: v => v < 30 ? 'Poor' : v < 60 ? 'Fair' : v < 85 ? 'Good' : 'Perfect',
    ranges: [
      { label: 'Poor', max: 30, color: '#d96a5c' },
      { label: 'Fair', min: 30, max: 60, color: '#d9a74a' },
      { label: 'Good', min: 60, max: 85, color: '#667eea' },
      { label: 'Perfect', min: 85, color: '#4a36a8' },
    ]
  },
  study: {
    label: 'Study Focus', unit: '', icon: 'study',
    description: 'Optimized for cognitive load. High light levels (> 400 lux) and fresh air (low VOCs) help maintain alertness and retention.',
    min: 0, max: 99,
    palette: { bg: '#fdf9f0', accent: '#d9a74a', iconBg: '#f9f2e2' },
    getStatus: v => v < 40 ? 'Poor' : v < 70 ? 'Moderate' : 'Focused',
    ranges: [
      { label: 'Poor', max: 40, color: '#d96a5c' },
      { label: 'Moderate', min: 40, max: 70, color: '#d9a74a' },
      { label: 'Focused', min: 70, color: '#4aab7a' },
    ]
  },
  work: {
    label: 'Work Flow', unit: '', icon: 'work',
    description: 'Balanced for sustained productivity. Keeps CO2/VOCs low to prevent brain fog while maintaining a comfortable thermal range.',
    min: 0, max: 99,
    palette: { bg: '#f0f7f9', accent: '#3272d9', iconBg: '#e2f0f2' },
    getStatus: v => v < 40 ? 'Sluggish' : v < 70 ? 'Steady' : 'Flow State',
    ranges: [
      { label: 'Sluggish', max: 40, color: '#d96a5c' },
      { label: 'Steady', min: 40, max: 70, color: '#3272d9' },
      { label: 'Flow State', min: 70, color: '#4aab7a' },
    ]
  },
  fun: {
    label: 'Social Energy', unit: '', icon: 'fun',
    description: 'The "Sparkle" factor. Measured by vibrant lighting and moderate noise levels that suit a lively social environment.',
    min: 0, max: 99,
    palette: { bg: '#f9f0f4', accent: '#fa709a', iconBg: '#f2e2e7' },
    getStatus: v => v < 40 ? 'Dull' : v < 70 ? 'Pleasant' : 'Vibrant',
    ranges: [
      { label: 'Dull', max: 40, color: '#9a948c' },
      { label: 'Pleasant', min: 40, max: 70, color: '#fa709a' },
      { label: 'Vibrant', min: 70, color: '#ff0080' },
    ]
  },
}

/* ─────────────────────────────────────────
   Unit Conversion Helpers
   ───────────────────────────────────────── */

const CONVERSIONS = {
  temperature_c: {
    imperial: { unit: '°F', convert: v => (v * 9/5) + 32, label: 'Temperature' },
    metric: { unit: '°C', convert: v => v, label: 'Temperature' }
  },
  pressure_hpa: {
    imperial: { unit: 'inHg', convert: v => v * 0.02953, label: 'Pressure' },
    metric: { unit: 'hPa', convert: v => v, label: 'Pressure' }
  }
}

function getConvertedValue(key, value, system) {
  if (value === null || value === undefined) return value
  if (CONVERSIONS[key]) {
    return CONVERSIONS[key][system].convert(value)
  }
  return value
}

function getConvertedUnit(key, system) {
  if (CONVERSIONS[key]) {
    return CONVERSIONS[key][system].unit
  }
  return SENSOR_META[key].unit
}

/* ─────────────────────────────────────────
   Modal Component
   ───────────────────────────────────────── */

export function SensorInfoDrawer({ meta, value, onClose, unitSystem }) {
  if (!meta) return null

  const sensorKey = Object.keys(SENSOR_META).find(k => SENSOR_META[k].label === meta.label)
  const displayValRaw = getConvertedValue(sensorKey, value, unitSystem)
  const displayVal = (displayValRaw === null || displayValRaw === undefined) ? '—' : typeof displayValRaw === 'number' ? displayValRaw.toFixed(1) : displayValRaw
  const statusWord = (value === null || value === undefined) ? 'Unknown' : meta.getStatus(value)
  const unit = getConvertedUnit(sensorKey, unitSystem)

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
            <p className="env-modal__subtitle">Currently sitting at <span style={{ color: meta.palette.accent, fontWeight: 700 }}>{displayVal}{unit}</span> ({statusWord})</p>
          </div>
        </div>

        <div className="env-modal__body">
          <p className="env-modal__desc">{meta.description}</p>
          
          <div className="env-modal__ranges">
            <h4 className="env-modal__section-title">Reference Ranges ({unitSystem === 'metric' ? 'Metric' : 'Imperial'})</h4>
            {meta.ranges.map((r, i) => {
              const rMin = getConvertedValue(sensorKey, r.min, unitSystem)
              const rMax = getConvertedValue(sensorKey, r.max, unitSystem)
              return (
                <div key={i} className="env-modal__range-item">
                  <div className="env-modal__range-color" style={{ background: r.color }} />
                  <span className="env-modal__range-label">{r.label}</span>
                  <span className="env-modal__range-val">
                    {rMin !== undefined && rMax !== undefined ? `${rMin.toFixed(rMin > 100 ? 0 : 1)} - ${rMax.toFixed(rMax > 100 ? 0 : 1)}` : 
                     rMin !== undefined ? `> ${rMin.toFixed(rMin > 100 ? 0 : 1)}` : 
                     `< ${rMax.toFixed(rMax > 100 ? 0 : 1)}`} {unit}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}

/* ─────────────────────────────────────────
   SensorCard
   ───────────────────────────────────────── */

function SensorCard({ sensorKey, value, onInfoClick, unitSystem }) {
  const meta = SENSOR_META[sensorKey]
  if (!meta) return null

  const isLoading = value === null || value === undefined
  const displayValRaw = getConvertedValue(sensorKey, value, unitSystem)
  const displayVal = isLoading ? '—' : typeof displayValRaw === 'number' ? displayValRaw.toFixed(1) : displayValRaw
  const statusWord = isLoading ? '' : meta.getStatus(value)
  const unit = getConvertedUnit(sensorKey, unitSystem)

  const barPercent = isLoading
    ? 0
    : Math.max(0, Math.min(100, ((value - meta.min) / (meta.max - meta.min)) * 100))

  return (
    <div
      className={`env-card ${isLoading ? 'env-card--loading' : ''}`}
      style={{ '--card-bg': meta.palette.bg, '--card-accent': meta.palette.accent, '--card-icon-bg': meta.palette.iconBg }}
      id={`sensor-${sensorKey}`}
    >
      <button 
        className="env-card__info-btn" 
        onClick={() => onInfoClick(sensorKey)}
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
        {!isLoading && <span className="env-card__unit">{unit}</span>}
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

export default function SensorGrid({ reading, onInfoClick, unitSystem }) {
  const keys = Object.keys(SENSOR_META)
  return (
    <div className="env-grid">
      {keys.map(key => (
        <SensorCard 
          key={key} 
          sensorKey={key} 
          value={reading ? reading[key] : null} 
          onInfoClick={onInfoClick}
          unitSystem={unitSystem}
        />
      ))}
    </div>
  )
}

export { SensorCard, SENSOR_META, Icons }
