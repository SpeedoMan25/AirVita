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
        <span className="scenario-panel__icon">🎮</span>
        <h3 className="scenario-panel__title">Simulation Controls</h3>
      </div>
      
      <div className="scenario-panel__grid">
        {scenarios.map((s) => (
          <button
            key={s.id}
            className={`scenario-btn ${s.id === activeId ? 'scenario-btn--active' : ''}`}
            onClick={() => onSelect(s.id)}
            id={`btn-scenario-${s.id}`}
          >
            <span className="scenario-btn__name">{s.name}</span>
          </button>
        ))}
      </div>
      
      <div className="scenario-panel__info">
        Selecting a preset pauses auto-cycling for 60s.
      </div>
    </div>
  );
}
