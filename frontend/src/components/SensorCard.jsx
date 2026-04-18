import React from 'react'
import './SensorCard.css'

/**
 * Sensor configurations:
 *   key, label, unit, icon, min/max for the bar, accent color
 */
const SENSOR_META = {
  temperature_c: {
    label: 'Temperature',
    unit: '°C',
    icon: '🌡️',
    min: 10,
    max: 40,
    accent: '#c47a5f',
  },
  humidity_pct: {
    label: 'Humidity',
    unit: '%RH',
    icon: '💧',
    min: 0,
    max: 100,
    accent: '#5b8fd9',
  },
  light_lux: {
    label: 'Light Level',
    unit: 'lux',
    icon: '☀️',
    min: 0,
    max: 1000,
    accent: '#d9a74a',
  },
  noise_db: {
    label: 'Noise Level',
    unit: 'dB',
    icon: '🔊',
    min: 0,
    max: 100,
    accent: '#8a75c0',
  },
  pressure_hpa: {
    label: 'Air Pressure',
    unit: 'hPa',
    icon: '🌀',
    min: 960,
    max: 1060,
    accent: '#5ba6b5',
  },
  pm25_ugm3: {
    label: 'Particles (PM2.5)',
    unit: 'µg/m³',
    icon: '🫁',
    min: 0,
    max: 150,
    accent: '#c75c5c',
  },
  voc_ppb: {
    label: 'VOCs',
    unit: 'ppb',
    icon: '🧪',
    min: 0,
    max: 1500,
    accent: '#4aba8a',
  },
}

/**
 * Return a color based on how good/bad a value is for its sensor type.
 */
function getBarColor(key, value) {
  const meta = SENSOR_META[key]
  if (!meta) return 'var(--accent-indigo)'
  return meta.accent
}

/**
 * SensorCard — Displays a single sensor reading with icon, value, and level bar.
 *
 * @param {Object} props
 * @param {string} props.sensorKey - key from SENSOR_META
 * @param {number|null} props.value - current reading
 */
function SensorCard({ sensorKey, value }) {
  const meta = SENSOR_META[sensorKey]
  if (!meta) return null

  const isLoading = value === null || value === undefined
  const barPercent = isLoading
    ? 0
    : Math.max(0, Math.min(100, ((value - meta.min) / (meta.max - meta.min)) * 100))

  return (
    <div
      className={`sensor-card ${isLoading ? 'sensor-card--loading' : ''}`}
      style={{ '--card-accent': meta.accent }}
      id={`sensor-${sensorKey}`}
    >
      <div className="sensor-card__icon">{meta.icon}</div>
      <span className="sensor-card__label">{meta.label}</span>
      <div className="sensor-card__value-row">
        <span className="sensor-card__value">
          {isLoading ? '---' : typeof value === 'number' ? value.toFixed(1) : value}
        </span>
        {!isLoading && <span className="sensor-card__unit">{meta.unit}</span>}
      </div>
      <div className="sensor-card__bar">
        <div
          className="sensor-card__bar-fill"
          style={{
            width: `${barPercent}%`,
            background: `linear-gradient(90deg, ${meta.accent}88, ${meta.accent})`,
          }}
        />
      </div>
    </div>
  )
}

/**
 * SensorGrid — Renders all sensor cards in a responsive grid.
 */
export default function SensorGrid({ reading }) {
  const sensorKeys = Object.keys(SENSOR_META)

  return (
    <div className="sensor-grid">
      {sensorKeys.map((key) => (
        <SensorCard
          key={key}
          sensorKey={key}
          value={reading ? reading[key] : null}
        />
      ))}
    </div>
  )
}

export { SensorCard, SENSOR_META }
