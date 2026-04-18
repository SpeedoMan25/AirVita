import React, { useMemo } from 'react'
import './ScoreGauge.css'

function getScoreColor(score) {
  if (score <= 0) return '#565d68'
  const t = Math.max(0, Math.min(1, (score - 1) / 98))
  const hue = Math.round(t * 145)
  const saturation = 45 + t * 20
  const lightness = 48 + t * 6
  return `hsl(${hue}, ${saturation}%, ${lightness}%)`
}

function getStatusText(score) {
  if (score <= 0) return 'Awaiting data'
  if (score <= 20) return 'Hazardous'
  if (score <= 40) return 'Poor'
  if (score <= 60) return 'Fair'
  if (score <= 75) return 'Good'
  if (score <= 90) return 'Great'
  return 'Excellent'
}

/**
 * ScoreGauge — Semi-circular meter for the Room Health Score.
 */
export default function ScoreGauge({ score = 0, connected = false }) {
  const color = useMemo(() => getScoreColor(score), [score])
  const status = useMemo(() => getStatusText(score), [score])

  const radius = 90
  const circumference = Math.PI * radius
  const progress = score > 0 ? (score / 99) * circumference : 0
  const strokeDashoffset = circumference - progress

  const gradientId = 'score-gradient'
  const arcPath = `M 20,110 A ${radius},${radius} 0 0 1 200,110`

  return (
    <div className="score-gauge">
      <div className="score-gauge__ring-container">
        <div className="score-gauge__pulse" />

        <svg className="score-gauge__svg" viewBox="0 0 220 130">
          <defs>
            <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#c75c5c" />
              <stop offset="50%" stopColor="#d9a74a" />
              <stop offset="100%" stopColor="#4aba8a" />
            </linearGradient>
          </defs>
          <path className="score-gauge__track" d={arcPath} />
          <path
            className="score-gauge__progress"
            d={arcPath}
            stroke={`url(#${gradientId})`}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
          />
        </svg>

        <div className="score-gauge__value-container">
          <span className="score-gauge__value" style={{ color }}>
            {score > 0 ? score : '--'}
          </span>
          <span className="score-gauge__label">Score</span>
        </div>
      </div>

      <div className="score-gauge__status-row">
        <span className="score-gauge__status" style={{ color }}>
          {status}
        </span>
        <div className="score-gauge__connection">
          <span className={`score-gauge__dot ${connected ? 'score-gauge__dot--connected' : 'score-gauge__dot--disconnected'}`} />
          {connected ? 'Connected' : 'Disconnected'}
        </div>
      </div>
    </div>
  )
}
