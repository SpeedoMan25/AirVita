import React from 'react';
import './ScenarioControls.css';

/**
 * ScenarioControls — Allows users to manually select simulation presets.
 * 
 * @param {Object} props
 * @param {Array} props.scenarios - List of available scenarios
 * @param {string} props.activeId - ID of currently active manual scenario (if any)
 * @param {Function} props.onSelect - Callback when a scenario is clicked
 */
export default function ScenarioControls({ scenarios, activeId, onSelect }) {
  if (!scenarios || scenarios.length === 0) return null;

  return (
    <div className="scenario-panel">
      <div className="scenario-panel__header">
        <span className="scenario-panel__icon">🧠</span>
        <div>
          <h3 className="scenario-panel__title">Environment Simulation</h3>
          <p className="scenario-panel__subtitle">Manual neural overrides active</p>
        </div>
      </div>
      
      <div className="scenario-panel__grid">
        {scenarios.map((s) => (
          <button
            key={s.id}
            className={`scenario-btn ${s.id === activeId ? 'scenario-btn--active' : ''}`}
            onClick={() => onSelect(s.id)}
            id={`btn-scenario-${s.id}`}
            title={s.name}
          >
            <span className="scenario-btn__icon">{s.icon || '📍'}</span>
            <span className="scenario-btn__name">{s.name}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
