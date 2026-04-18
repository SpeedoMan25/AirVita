import React, { useMemo } from 'react'
import './ScoreGauge.css'

function getSleepColor(score) {
  if (score <= 0) return '#ccc'
  if (score <= 30) return '#ff7eb3' // Soft reddish/pink for poor sleep
  if (score <= 50) return '#a18cd1' // Muted purple
  if (score <= 70) return '#4facfe' // Calm blue
  if (score <= 85) return '#00f2fe' // Bright aqua
  return '#667eea' // Deep sleep indigo
}

function getSleepWord(score) {
  if (score <= 0) return 'Analyzing...'
  if (score <= 30) return 'Poor for Sleep'
  if (score <= 50) return 'Sub-optimal'
  if (score <= 70) return 'Acceptable'
  if (score <= 85) return 'Good Quality'
  return 'Perfect for Sleep'
}

function getSleepEmoji(score) {
  return null
}

export default function SleepScoreGauge({ score = 0 }) {
  const color = useMemo(() => getSleepColor(score), [score])
  const word = useMemo(() => getSleepWord(score), [score])
  const emoji = useMemo(() => getSleepEmoji(score), [score])

  const radius = 90
  const circumference = Math.PI * radius
  const progress = score > 0 ? (score / 99) * circumference : 0
  const dashoffset = circumference - progress

  const arcPath = `M 20,110 A ${radius},${radius} 0 0 1 200,110`

  return (
    <div className="score-card score-card--sleep" id="sleep-gauge">
      <div className="score-card__top">
        <span className="score-card__heading">Sleep Conditions</span>
      </div>

      <div className="score-card__gauge">
        <svg className="score-card__svg" viewBox="0 0 220 125" aria-hidden="true">
          <defs>
            <linearGradient id="sleepArc" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#ff7eb3" />
              <stop offset="45%" stopColor="#a18cd1" />
              <stop offset="100%" stopColor="#667eea" />
            </linearGradient>
          </defs>
          <path className="score-card__track" d={arcPath} />
          <path
            className="score-card__fill"
            d={arcPath}
            stroke="url(#sleepArc)"
            strokeDasharray={circumference}
            strokeDashoffset={dashoffset}
          />
        </svg>

        <div className="score-card__number-wrap">
          <span className="score-card__number" style={{ color }}>
            {score > 0 ? score : '—'}
          </span>
          <span className="score-card__of">/99</span>
        </div>
      </div>

      <div className="score-card__bottom">
        <span className="score-card__word" style={{ color }}>{word}</span>
        <span className="score-card__desc">
          {score > 85
            ? 'Environment is ideal for deep rest.'
            : score > 60
            ? 'Conditions are conducive to sleep.'
            : score > 0
            ? 'Consider dimming light or cooling down.'
            : 'Calculating sleep suitability...'}
        </span>
      </div>
    </div>
  )
}
