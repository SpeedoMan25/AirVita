import React from 'react'
import './AISummary.css'

/**
 * AISummary — Displays the environment analysis from Gemini.
 */
export default function AISummary({ summary, flags = [], loading, error, onRefresh }) {
  return (
    <div className="ai-summary" id="ai-summary">
      <div className="ai-summary__header">
        <h2 className="ai-summary__title">Analysis</h2>
        <button
          className="ai-summary__refresh-btn"
          onClick={onRefresh}
          disabled={loading}
          id="refresh-analysis-btn"
          aria-label="Run analysis"
        >
          {loading ? 'Running...' : 'Run Analysis'}
        </button>
      </div>

      <div className="ai-summary__body">
        {error && (
          <p className="ai-summary__error" role="alert">{error}</p>
        )}

        {!error && !loading && !summary && (
          <p className="ai-summary__placeholder">
            Click <strong>Run Analysis</strong> to generate a health report based on current sensor readings.
          </p>
        )}

        {!error && loading && (
          <div className="ai-summary__skeleton">
            <div className="ai-summary__skeleton-line" style={{ width: '90%' }} />
            <div className="ai-summary__skeleton-line" style={{ width: '75%' }} />
            <div className="ai-summary__skeleton-line" style={{ width: '60%' }} />
          </div>
        )}

        {!error && !loading && summary && (
          <>
            <p className="ai-summary__text">{summary}</p>

            {flags.length > 0 && (
              <ul className="ai-summary__flags">
                {flags.map((flag, i) => (
                  <li key={i} className="ai-summary__flag">
                    <span className="ai-summary__flag-dot" />
                    {flag}
                  </li>
                ))}
              </ul>
            )}

            {flags.length === 0 && (
              <p className="ai-summary__clear">All readings within recommended ranges.</p>
            )}
          </>
        )}
      </div>

      <div className="ai-summary__footer">
        <span>Powered by Gemini</span>
      </div>
    </div>
  )
}
