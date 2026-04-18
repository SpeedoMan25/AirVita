import React, { useMemo } from 'react'
import './ScoreGauge.css'

function getScoreColor(score) {
  if (score <= 0) return '#ccc'
  if (score <= 30) return '#d96a5c'
  if (score <= 50) return '#d9a74a'
  if (score <= 70) return '#b8b048'
  if (score <= 85) return '#6aab6a'
  return '#4aab7a'
}

function getStatusWord(score) {
  if (score <= 0) return 'Waiting...'
  if (score <= 20) return 'Poor'
  if (score <= 40) return 'Fair'
  if (score <= 60) return 'Moderate'
  if (score <= 75) return 'Good'
  if (score <= 90) return 'Very Good'
  return 'Excellent'
}

function getEmoji(score) {
  if (score <= 0) return '🏠'
  if (score <= 40) return '😕'
  if (score <= 60) return '🙂'
  if (score <= 80) return '😊'
  return '🌿'
}

export default function ScoreGauge({ score = 0 }) {
  const color = useMemo(() => getScoreColor(score), [score])
  const word = useMemo(() => getStatusWord(score), [score])
  const emoji = useMemo(() => getEmoji(score), [score])

  const radius = 90
  const circumference = Math.PI * radius
  const progress = score > 0 ? (score / 99) * circumference : 0
  const dashoffset = circumference - progress

  const arcPath = `M 20,110 A ${radius},${radius} 0 0 1 200,110`

  return (
    <div className="score-card" id="score-gauge">
      <div className="score-card__top">
        <span className="score-card__emoji">{emoji}</span>
        <span className="score-card__heading">Room Health</span>
      </div>

      <div className="score-card__gauge">
        <svg className="score-card__svg" viewBox="0 0 220 125" aria-hidden="true">
          <defs>
            <linearGradient id="scoreArc" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#d96a5c" />
              <stop offset="45%" stopColor="#d9a74a" />
              <stop offset="100%" stopColor="#4aab7a" />
            </linearGradient>
          </defs>
          <path className="score-card__track" d={arcPath} />
          <path
            className="score-card__fill"
            d={arcPath}
            stroke="url(#scoreArc)"
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
          {score > 75
            ? 'Your room feels great right now.'
            : score > 50
            ? 'Room conditions are acceptable.'
            : score > 0
            ? 'Some readings need attention.'
            : 'Connecting to sensors...'}
        </span>
      </div>
    </div>
  )
}
