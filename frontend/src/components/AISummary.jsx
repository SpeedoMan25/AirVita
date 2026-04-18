import React from 'react'
import './AISummary.css'

/**
 * AISummary — Displays the Gemini AI analysis of the current room environment.
 *
 * @param {Object}   props
 * @param {string}   props.summary    - AI-generated summary text
 * @param {string[]} props.flags      - Array of concern strings
 * @param {boolean}  props.loading    - Whether analysis is in progress
 * @param {string}   props.error      - Error message if fetch failed
 * @param {Function} props.onRefresh  - Callback to re-run analysis
 */
export default function AISummary({ summary, flags = [], loading, error, onRefresh }) {
  return (
    <div className="ai-summary" id="ai-summary">
      {/* Header row */}
      <div className="ai-summary__header">
        <div className="ai-summary__title-group">
          <span className="ai-summary__icon">✨</span>
          <h2 className="ai-summary__title">AI Analysis</h2>
          <span className="ai-summary__badge">Gemini 2.0 Flash</span>
        </div>
        <button
          className={`ai-summary__refresh-btn ${loading ? 'ai-summary__refresh-btn--loading' : ''}`}
          onClick={onRefresh}
          disabled={loading}
          id="refresh-analysis-btn"
          aria-label="Refresh AI analysis"
        >
          <span className="ai-summary__refresh-icon">{loading ? '⏳' : '🔄'}</span>
          {loading ? 'Analyzing…' : 'Refresh Analysis'}
        </button>
      </div>

      {/* Content */}
      <div className="ai-summary__body">
        {error && (
          <p className="ai-summary__error" role="alert">
            ⚠️ {error}
          </p>
        )}

        {!error && !loading && !summary && (
          <p className="ai-summary__placeholder">
            Click <strong>Refresh Analysis</strong> to get an AI-powered summary of your room's current environment.
          </p>
        )}

        {!error && (loading || summary) && (
          <>
            {/* Summary text */}
            <p className={`ai-summary__text ${loading ? 'ai-summary__text--skeleton' : 'ai-summary__text--visible'}`}>
              {loading ? '\u00A0' : summary}
            </p>

            {/* Flags */}
            {!loading && flags.length > 0 && (
              <div className="ai-summary__flags">
                <span className="ai-summary__flags-label">Concerns:</span>
                <div className="ai-summary__flags-list">
                  {flags.map((flag, i) => (
                    <span key={i} className="ai-summary__flag-chip">
                      ⚠️ {flag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {!loading && flags.length === 0 && summary && (
              <div className="ai-summary__all-clear">
                <span>✅ All readings within healthy ranges</span>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
