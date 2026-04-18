import React from 'react';
import './CalculationMath.css';

/**
 * CalculationMath — Component showing the mathematical breakdown of the Room Health Score.
 * 
 * @param {Object} props
 * @param {Object} props.breakdown - { base_mlp_score, voc_penalty, pm25_penalty, final_score }
 */
export default function CalculationMath({ breakdown }) {
  if (!breakdown) return null;

  const { base_mlp_score, voc_penalty, pm25_penalty, final_score } = breakdown;

  return (
    <div className="math-card" id="calculation-breakdown">
      <div className="math-card__header">
        <span className="math-card__icon">🧬</span>
        <h3 className="math-card__title">Scoring Algorithm</h3>
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
        Score = MLP + (VOC × -0.02) + (PM2.5 × -0.05)
      </div>
    </div>
  );
}
