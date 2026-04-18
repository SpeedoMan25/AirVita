import React from 'react'
import './AISummary.css'

/**
 * AISummary — Environment analysis panel.
 * Lively edition: uses friendly icons and a card-like layout.
 */
export default function AISummary({ summary, flags = [], loading, error, onRefresh }) {
  return (
    <div className="insight-card" id="ai-summary">
      <div className="insight-card__header">
        <div className="insight-card__title-wrap">
          <span className="insight-card__icon">✨</span>
          <h3 className="insight-card__title">Room Analysis</h3>
        </div>
        <button
          className="insight-card__btn"
          onClick={onRefresh}
          disabled={loading}
          id="refresh-analysis-btn"
        >
          {loading ? 'Thinking...' : 'Run Update'}
        </button>
      </div>

      <div className="insight-card__body">
        {error && (
          <div className="insight-card__error">
            <span>⚠️</span> {error}
          </div>
        )}

        {!error && !loading && !summary && (
          <div className="insight-card__placeholder">
            <p>Tap "Run Update" to get an AI-powered breakdown of your room's health.</p>
          </div>
        )}

        {!error && loading && (
          <div className="insight-card__loading">
            <div className="insight-card__skeleton" style={{ width: '100%' }} />
            <div className="insight-card__skeleton" style={{ width: '85%' }} />
            <div className="insight-card__skeleton" style={{ width: '60%' }} />
          </div>
        )}

        {!error && !loading && summary && (
          <div className="insight-card__content">
            <p className="insight-card__text">{summary}</p>

            {flags.length > 0 && (
              <div className="insight-card__alerts">
                <span className="insight-card__alert-label">Points of Attention:</span>
                <ul className="insight-card__list">
                  {flags.map((flag, i) => (
                    <li key={i} className="insight-card__item">
                      <span className="insight-card__dot" /> {flag}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {flags.length === 0 && (
              <div className="insight-card__success">
                <span>✅</span> Everything looks great!
              </div>
            )}
          </div>
        )}
      </div>

      <div className="insight-card__footer">
        Powered by Gemini Flash
      </div>
    </div>
  )
}
