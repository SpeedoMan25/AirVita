import React, { useMemo } from 'react'
import './ScoreGauge.css'

/**
 * Returns a CSS color on the red→orange→yellow→green gradient
 * based on a score from 1 (deep red) to 99 (bright green).
 */
function getScoreColor(score) {
  if (score <= 0) return '#6b7280' // gray for no data
  // Normalize score 1-99 to 0-1
  const t = Math.max(0, Math.min(1, (score - 1) / 98))

  // HSL interpolation: 0° (red) → 142° (green)
  const hue = Math.round(t * 142)
  const saturation = 75 + t * 10  // 75% → 85%
  const lightness = 45 + t * 10   // 45% → 55%

  return `hsl(${hue}, ${saturation}%, ${lightness}%)`
}

/**
 * Returns a gradient string for the SVG stroke.
 */
function getScoreGradient(score) {
  if (score <= 25) return { from: '#dc2626', to: '#ef4444' }      // Deep red
  if (score <= 50) return { from: '#ea580c', to: '#f97316' }      // Orange
  if (score <= 75) return { from: '#ca8a04', to: '#22c55e' }      // Yellow → Green
  return { from: '#16a34a', to: '#10b981' }                        // Bright green
}

function getStatusText(score) {
  if (score <= 0) return 'Awaiting Data'
  if (score <= 20) return '⚠️ Hazardous'
  if (score <= 40) return '😟 Poor'
  if (score <= 60) return '😐 Fair'
  if (score <= 75) return '🙂 Good'
  if (score <= 90) return '😊 Great'
  return '🌟 Excellent'
}

/**
 * ScoreGauge — Semi-circular SVG meter displaying the Room Health Score.
 *
 * @param {Object} props
 * @param {number} props.score - 0–99 (0 = no data)
 * @param {boolean} props.connected - serial connection status
 */
export default function ScoreGauge({ score = 0, connected = false }) {
  const color = useMemo(() => getScoreColor(score), [score])
  const gradient = useMemo(() => getScoreGradient(score), [score])
  const status = useMemo(() => getStatusText(score), [score])

  // SVG math for semi-circle
  const radius = 90
  const circumference = Math.PI * radius // Half-circle length
  const progress = score > 0 ? (score / 99) * circumference : 0
  const strokeDashoffset = circumference - progress

  const gradientId = 'score-gradient'

  // Path for 180deg arc: M startX startY A radiusX radiusY rotation largeArc sweepX endX
  // Starts at left (20, 110) and ends at right (200, 110)
  const arcPath = `M 20,110 A ${radius},${radius} 0 0 1 200,110`

  return (
    <div className="score-gauge">
      <div className="score-gauge__ring-container" style={{ '--gauge-glow': `${color}40` }}>
        {/* Pulse ring */}
        <div
          className="score-gauge__pulse"
          style={{ borderColor: `${color}30` }}
        />

        {/* SVG Arc */}
        <svg className="score-gauge__svg" viewBox="0 0 220 130">
          <defs>
            <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#ef4444" />
              <stop offset="50%" stopColor="#eab308" />
              <stop offset="100%" stopColor="#22c55e" />
            </linearGradient>
          </defs>
          <path
            className="score-gauge__track"
            d={arcPath}
          />
          <path
            className="score-gauge__progress"
            d={arcPath}
            stroke={`url(#${gradientId})`}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
          />
        </svg>

        {/* Center value */}
        <div className="score-gauge__value-container">
          <span className="score-gauge__value" style={{ color }}>
            {score > 0 ? score : '—'}
          </span>
          <span className="score-gauge__label">Room Score</span>
        </div>
      </div>

      {/* Status badge */}
      <div className="score-gauge__status" style={{ color, borderColor: `${color}30` }}>
        {status}
      </div>

      {/* Connection indicator */}
      <div className="score-gauge__connection">
        <span className={`score-gauge__dot ${connected ? 'score-gauge__dot--connected' : 'score-gauge__dot--disconnected'}`} />
        {connected ? 'Sensor Connected' : 'Sensor Disconnected'}
      </div>
    </div>
  )
}
