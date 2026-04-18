import React from 'react';
import './CalculationMath.css';

/**
 * CalculationMath — Component showing the mathematical breakdown of scores.
 * 
 * Supports two modes:
 * 1. Health (Health IAQ) - MLP + Penalties
 * 2. Activity (Sleep, Study, etc.) - Weighted Sensorts
 */
export default function CalculationMath({ breakdown }) {
  if (!breakdown) return null;

  // Mode 1: Health / IAQ (Legacy MLP style)
  if (breakdown.final_score !== undefined) {
    const { base_mlp_score, voc_penalty, pm25_penalty, final_score } = breakdown;
    return (
      <div className="math-card" id="calculation-breakdown">
        <div className="math-card__header">
          <span className="math-card__icon">🧬</span>
          <h3 className="math-card__title">Health Algorithm</h3>
        </div>
        
        <div className="math-card__content">
          <div className="math-row">
            <div className="math-row__label">Neural Net Base</div>
            <div className="math-row__value">{base_mlp_score.toFixed(1)}</div>
          </div>

          <div className={`math-row ${voc_penalty < 0 ? 'math-row--penalty' : ''}`}>
            <div className="math-row__label">VOC Impact</div>
            <div className="math-row__value">
              {voc_penalty < 0 ? '-' : ''}{Math.abs(voc_penalty).toFixed(1)}
            </div>
          </div>

          <div className={`math-row ${pm25_penalty < 0 ? 'math-row--penalty' : ''}`}>
            <div className="math-row__label">PM2.5 Impact</div>
            <div className="math-row__value">
              {pm25_penalty < 0 ? '-' : ''}{Math.abs(pm25_penalty).toFixed(1)}
            </div>
          </div>

          <div className="math-divider"></div>

          <div className="math-row math-row--total">
            <div className="math-row__label">Final IAQ</div>
            <div className="math-row__value">{final_score}</div>
          </div>
        </div>
        
        <div className="math-card__footer">
          Equation: MLP + (VOC × -0.02) + (PM2.5 × -0.05)
        </div>
      </div>
    );
  }

  // Mode 2: Activity (Weighted factors)
  if (breakdown.type === 'weighted') {
    const { activity, factors } = breakdown;
    const title = activity.charAt(0).toUpperCase() + activity.slice(1);
    
    return (
      <div className="math-card" id="activity-breakdown">
        <div className="math-card__header">
          <span className="math-card__icon">📊</span>
          <h3 className="math-card__title">{title} Math</h3>
        </div>

        <div className="math-card__content">
          {factors && factors.length > 0 ? factors.map((f, i) => (
            <div key={i} className={`math-row ${f.sub_score < 50 ? 'math-row--penalty' : ''}`}>
              <div className="math-row__label">
                {f.sensor.split('_')[0]} 
                <span className="math-row__sub">({(f.weight * 100).toFixed(0)}% weight)</span>
              </div>
              <div className="math-row__value">
                {f.points.toFixed(1)}
              </div>
            </div>
          )) : (
            <div className="math-row">Connecting to sensors...</div>
          )}

          <div className="math-divider"></div>

          <div className="math-card__footer">
            Final score is the weighted average of sub-scores (clamped 1-99).
          </div>
        </div>
      </div>
    );
  }

  return null;
}
