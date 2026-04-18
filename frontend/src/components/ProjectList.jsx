import React, { useState } from 'react'
import './Simulator.css'

const ARCHETYPES = {
  ideal: {
    name: "Ideal",
    humidity: 45,
    pressure: 1013,
    light: 500,
    temperature: 22,
    sound_high: 10,
    sound_mid: 15,
    sound_low: 20,
    sound_amp: 15,
    vocs: 50,
    particulates: 5
  },
  wildfire: {
    name: "Wildfire",
    humidity: 15,
    pressure: 1005,
    light: 200,
    temperature: 35,
    sound_high: 10,
    sound_mid: 15,
    sound_low: 20,
    sound_amp: 15,
    vocs: 800,
    particulates: 250
  },
  party: {
    name: "Party",
    humidity: 55,
    pressure: 1010,
    light: 800,
    temperature: 26,
    sound_high: 80,
    sound_mid: 90,
    sound_low: 70,
    sound_amp: 85,
    vocs: 400,
    particulates: 20
  },
  stuffy: {
    name: "Stuffy",
    humidity: 85,
    pressure: 1015,
    light: 50,
    temperature: 18,
    sound_high: 5,
    sound_mid: 5,
    sound_low: 5,
    sound_amp: 5,
    vocs: 1200,
    particulates: 10
  }
}

export default function Simulator({ onSimulate }) {
  const [formData, setFormData] = useState(ARCHETYPES.ideal)
  const [loading, setLoading] = useState(false)

  const handleArchetypeClick = (key) => {
    setFormData(ARCHETYPES[key])
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: parseFloat(value) || 0 }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const response = await fetch('/api/sensor-data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })
      if (!response.ok) throw new Error('Simulation failed')
      await onSimulate() // Refresh app status
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="simulator">
      <h3>Simulation Control</h3>
      <div className="simulator__archetypes">
        {Object.keys(ARCHETYPES).map(key => (
          <button 
            key={key} 
            className="simulator__btn" 
            onClick={() => handleArchetypeClick(key)}
          >
            {ARCHETYPES[key].name}
          </button>
        ))}
      </div>

      <form className="simulator__form" onSubmit={handleSubmit}>
        <div className="simulator__grid">
          {Object.keys(formData).filter(k => k !== 'name').map(key => (
            <div key={key} className="simulator__input-group">
              <label>{key.replace('_', ' ')}</label>
              <input 
                type="number" 
                name={key} 
                value={formData[key]} 
                onChange={handleChange}
                step="0.1"
              />
            </div>
          ))}
        </div>
        <button type="submit" className="simulator__submit" disabled={loading}>
          {loading ? 'Simulating...' : 'Apply Simulation Data'}
        </button>
      </form>
    </div>
  )
}
