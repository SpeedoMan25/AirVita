import React, { useMemo } from 'react'
import { Icons } from './SensorCard'
import './ScoreGauge.css'

const CONFIGS = {
  health: {
    title: 'Room Health',
    gradient: ['#d96a5c', '#d9a74a', '#4aab7a'],
    getWord: (s) => {
      if (s <= 20) return 'Poor';
      if (s <= 40) return 'Fair';
      if (s <= 60) return 'Moderate';
      if (s <= 75) return 'Good';
      return 'Excellent';
    }
  },
  sleep: {
    title: 'Sleep quality',
    gradient: ['#ff7eb3', '#a18cd1', '#667eea'],
    getWord: (s) => {
      if (s <= 30) return 'Poor';
      if (s <= 50) return 'Sub-optimal';
      if (s <= 70) return 'Acceptable';
      if (s <= 85) return 'Good Quality';
      return 'Perfect';
    }
  },
  study: {
    title: 'Study Focus',
    gradient: ['#f6d365', '#fda085', '#f093fb'],
    getWord: (s) => {
      if (s <= 40) return 'Distracted';
      if (s <= 60) return 'Moderate';
      if (s <= 80) return 'Focused';
      return 'Deep Focus';
    }
  },
  work: {
    title: 'Work Flow',
    gradient: ['#84fab0', '#8fd3f4', '#209cff'],
    getWord: (s) => {
      if (s <= 40) return 'Stagnant';
      if (s <= 65) return 'Efficient';
      return 'Peak Flow';
    }
  },
  fun: {
    title: 'Social/Fun',
    gradient: ['#fa709a', '#fee140', '#ff0080'],
    getWord: (s) => {
      if (s <= 40) return 'Dull';
      if (s <= 70) return 'Pleasant';
      return 'Vibrant';
    }
  }
};

export default function ScoreGauge({ type = 'health', score = 0, isActive = false, onClick, onInfoClick }) {
  const config = CONFIGS[type] || CONFIGS.health;
  const word = useMemo(() => config.getWord(score), [score, config]);

  const radius = 90;
  const circumference = Math.PI * radius;
  const progress = score > 0 ? (score / 99) * circumference : 0;
  const dashoffset = circumference - progress;

  const arcPath = `M 20,110 A ${radius},${radius} 0 0 1 200,110`;
  const gradId = `grad-${type}`;

  return (
    <div 
      className={`score-card score-card--${type} ${isActive ? 'score-card--active' : ''}`} 
      id={`${type}-gauge`}
      onClick={onClick}
      style={{ cursor: 'pointer', position: 'relative' }}
    >
      <button 
        className="env-card__info-btn" 
        onClick={(e) => {
          e.stopPropagation();
          onInfoClick(type);
        }}
        title={`More about ${config.title}`}
      >
        {Icons.info}
      </button>

      <div className="score-card__top">
        <span className="score-card__heading">{config.title}</span>
      </div>

      <div className="score-card__gauge">
        <svg className="score-card__svg" viewBox="0 0 220 125" aria-hidden="true">
          <defs>
            <linearGradient id={gradId} x1="0%" y1="0%" x2="100%" y2="0%">
              {config.gradient.map((color, i) => (
                <stop key={i} offset={`${(i / (config.gradient.length - 1)) * 100}%`} stopColor={color} />
              ))}
            </linearGradient>
          </defs>
          <path className="score-card__track" d={arcPath} />
          <path
            className="score-card__fill"
            d={arcPath}
            stroke={`url(#${gradId})`}
            strokeDasharray={circumference}
            strokeDashoffset={dashoffset}
          />
        </svg>

        <div className="score-card__number-wrap">
          <span className="score-card__number">
            {score > 0 ? score : '—'}
          </span>
          <span className="score-card__of">/99</span>
        </div>
      </div>

      <div className="score-card__bottom">
        <span className="score-card__word">{word}</span>
      </div>
    </div>
  );
}
