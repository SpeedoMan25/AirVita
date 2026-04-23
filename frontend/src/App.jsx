import React, { useState, useEffect, useCallback, useRef } from 'react'
import {
  Activity, Thermometer, Droplets, Sun, Volume2, Gauge, Wind,
  Settings2, X, RefreshCw, AlertCircle, BrainCircuit,
  CheckCircle2, ChevronRight, Camera, Radio, Crosshair, Cpu
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels'

import RoomScanner from './components/RoomScanner'
import MobilePairing from './components/MobilePairing'

const API_BASE = import.meta.env.DEV ? '' : (import.meta.env.VITE_API_URL || '')
const POLL_INTERVAL_MS = 500

/* ═══════════════════════════════════════════════════
   HUD SENSOR & ACTIVITY METADATA
   ═══════════════════════════════════════════════════ */

const SENSOR_META = {
  temperature_c: {
    label: 'Temperature', shortLabel: 'TEMP', unit: '°C', icon: Thermometer,
    iconColor: '#f43f5e', 
    min: 10, max: 40,
    getStatus: v => v < 15 ? 'FREEZING' : v < 18 ? 'COLD' : v < 20 ? 'COOL' : v <= 24 ? 'IDEAL' : v <= 27 ? 'WARM' : v <= 32 ? 'HOT' : 'SEARING',
    ranges: [
      { label: 'Freezing', max: 15, color: '#1e40af', text: 'Significant risk of hypothermia or muscle stiffness over time.' },
      { label: 'Cold', max: 18, color: '#3b82f6', text: 'Uncomfortably chilly. Circulation slows; fine with heavy layers.' },
      { label: 'Cool', max: 20, color: '#0ea5e9', text: 'Slightly below ideal. Manageable, but may affect manual dexterity.' },
      { label: 'Ideal', max: 24, color: '#10b981', text: 'Optimal thermal comfort for metabolic health and cognitive focus.' },
      { label: 'Warm', max: 27, color: '#fb923c', text: 'Comfortable, but core body temperature may begin to rise slightly.' },
      { label: 'Hot', max: 32, color: '#f43f5e', text: 'Increased perspiration and fatigue. Cognitive throughput begins to dip.' },
      { label: 'Searing', max: 40, color: '#9f1239', text: 'Extreme heat stress. Dehydration risk and acute discomfort.' },
    ],
  },
  humidity_pct: {
    label: 'Humidity', shortLabel: 'HUMIDITY', unit: '%', icon: Droplets,
    iconColor: '#0ea5e9', 
    min: 0, max: 100,
    getStatus: v => v < 20 ? 'ARID' : v < 35 ? 'DRY' : v < 45 ? 'LOW' : v <= 55 ? 'BALANCED' : v <= 65 ? 'SOFT' : v <= 75 ? 'HUMID' : 'DAMP',
    ranges: [
      { label: 'Arid', max: 20, color: '#f59e0b', text: 'Severe dryness. Significant risk of sinus irritation and static buildup.' },
      { label: 'Dry', max: 35, color: '#fb923c', text: 'Dry air may cause skin irritation and dry eyes over long periods.' },
      { label: 'Low', max: 45, color: '#0ea5e9', text: 'Slightly dry but comfortable for most; safe for electronics.' },
      { label: 'Balanced', max: 55, color: '#10b981', text: 'The "Goldilocks" zone for respiratory health and structural integrity.' },
      { label: 'Soft', max: 65, color: '#fbbf24', text: 'Pleasant, moist air. Good for plants, but monitor for condensation.' },
      { label: 'Humid', max: 75, color: '#f43f5e', text: 'Muggy feeling. Significant risk of mold growth in unventilated areas.' },
      { label: 'Damp', max: 100, color: '#9f1239', text: 'Extreme moisture. High risk of structural damage and bacterial growth.' },
    ],
  },
  light_lux: {
    label: 'Light', shortLabel: 'LUX', unit: 'lux', icon: Sun,
    iconColor: '#fbbf24', 
    min: 0, max: 1000,
    getStatus: v => v < 5 ? 'VOID' : v < 50 ? 'DIM' : v < 200 ? 'LOW' : v <= 500 ? 'OPTIMAL' : v <= 750 ? 'BRIGHT' : v <= 1000 ? 'INTENSE' : 'BLINDING',
    ranges: [
      { label: 'Void', max: 5, color: '#4c1d95', text: 'Total darkness. Optimal for deep melatonin production.' },
      { label: 'Dim', max: 50, color: '#8b5cf6', text: 'Soft ambient light. Good for pre-sleep relaxation or cinema.' },
      { label: 'Low', max: 200, color: '#0ea5e9', text: 'Casual indoor lighting. May cause eye strain for long-form reading.' },
      { label: 'Optimal', max: 500, color: '#10b981', text: 'Professional task lighting. Ideal for focus, detail work, and study.' },
      { label: 'Bright', max: 750, color: '#fbbf24', text: 'Energizing daylight levels. Great for alertness and social areas.' },
      { label: 'Intense', max: 1000, color: '#f43f5e', text: 'High intensity. May cause glare and digital screen washing.' },
      { label: 'Blinding', max: 2000, color: '#9f1239', text: 'Extreme brightness. Risk of acute eye fatigue and discomfort.' },
    ],
  },
  noise_db: {
    label: 'Noise', shortLabel: 'NOISE', unit: 'dB', icon: Volume2,
    iconColor: '#8b5cf6', 
    min: 0, max: 100,
    getStatus: v => v < 20 ? 'VOID' : v < 30 ? 'SILENT' : v < 45 ? 'QUIET' : v <= 55 ? 'MODERATE' : v <= 65 ? 'ACTIVE' : v <= 80 ? 'LOUD' : 'NOISY',
    ranges: [
      { label: 'Void', max: 20, color: '#064e3b', text: 'Absolute silence. Anechoic chamber levels; can be unsettling.' },
      { label: 'Silent', max: 30, color: '#10b981', text: 'Ideal for deep rest and high-stakes concentration.' },
      { label: 'Quiet', max: 45, color: '#0ea5e9', text: 'Soft background hum. Equivalent to a quiet library or office.' },
      { label: 'Moderate', max: 55, color: '#fbbf24', text: 'Normal conversation level. Common for living environments.' },
      { label: 'Active', max: 65, color: '#fb923c', text: 'Busy office or restaurant levels. Focus begins to fragment.' },
      { label: 'Loud', max: 80, color: '#f43f5e', text: 'Sustained exposure may cause stress and elevated heart rate.' },
      { label: 'Noisy', max: 100, color: '#9f1239', text: 'Hazardous for long-term exposure. Hearing fatigue likely.' },
    ],
  },
  pressure_hpa: {
    label: 'Pressure', shortLabel: 'PRESSURE', unit: 'hPa', icon: Gauge,
    iconColor: '#10b981', 
    min: 960, max: 1060,
    getStatus: v => v < 980 ? 'DEPRESSED' : v < 1000 ? 'LOW' : v < 1013 ? 'STANDARD' : v <= 1025 ? 'STABLE' : v <= 1040 ? 'HIGH' : v <= 1055 ? 'EXTREME' : 'SEVERE',
    ranges: [
      { label: 'Depressed', max: 980, color: '#4c1d95', text: 'Severe low pressure. High risk of storms and joint discomfort.' },
      { label: 'Low', max: 1000, color: '#8b5cf6', text: 'Unsettled weather patterns. Possible weather-related headaches.' },
      { label: 'Standard', max: 1013, color: '#0ea5e9', text: 'Typical sea-level pressure. Generally stable conditions.' },
      { label: 'Stable', max: 1025, color: '#10b981', text: 'Ideal atmospheric conditions. Clear and calm weather likely.' },
      { label: 'High', max: 1040, color: '#fbbf24', text: 'Anti-cyclonic conditions. Dry, sinking air and clear skies.' },
      { label: 'Extreme', max: 1055, color: '#f43f5e', text: 'Abnormally high pressure. May indicate unusual weather systems.' },
      { label: 'Severe', max: 1100, color: '#9f1239', text: 'Critical pressure variance. Sensor should be recalibrated.' },
    ],
  },
  pm25_ugm3: {
    label: 'PM 2.5', shortLabel: 'PARTICLES', unit: 'µg/m³', icon: Wind,
    iconColor: '#fb923c', 
    min: 0, max: 150,
    getStatus: v => v < 5 ? 'PRISTINE' : v < 12 ? 'CLEAN' : v < 25 ? 'MODERATE' : v < 35 ? 'FAIR' : v < 55 ? 'UNHEALTHY' : v < 100 ? 'POOR' : 'HAZARDOUS',
    ranges: [
      { label: 'Pristine', max: 5, color: '#059669', text: 'Laboratory-grade air. Zero detectable particulates.' },
      { label: 'Clean', max: 12, color: '#10b981', text: 'Excellent indoor air quality. Safe for all health groups.' },
      { label: 'Moderate', max: 25, color: '#fbbf24', text: 'Acceptable levels for short periods. Minimal health impact.' },
      { label: 'Fair', max: 35, color: '#f59e0b', text: 'Noticeable haze possible. Sensitive groups should monitor.' },
      { label: 'Unhealthy', max: 55, color: '#fb923c', text: 'Particulate load begins to stress respiratory defenses.' },
      { label: 'Poor', max: 100, color: '#f43f5e', text: 'Visible smog. Health risks for elderly and children.' },
      { label: 'Hazardous', max: 200, color: '#9f1239', text: 'Dangerous concentration. Use HEPA filtration immediately.' },
    ],
  }
}

const ACTIVITY_META = {
  health: {
    label: 'HEALTH BALANCE', id: 'health', color: '#10b981', sub: 'Bio-Metric Wellness',
    ranges: [
      { label: 'Hazardous', max: 15, color: '#f43f5e', text: 'Extreme particulates (>75µg) or humidity (>80%) detected. High risk of mold bloom or immediate illness.' },
      { label: 'Critical', max: 30, color: '#e11d48', text: 'Substantial PM2.5 levels detected. Respiratory irritation and eye strain likely for all occupants.' },
      { label: 'Poor', max: 45, color: '#fb923c', text: 'Stagnant air and thermal imbalances. Environment actively draining energy and immune system reserves.' },
      { label: 'Fair', max: 60, color: '#fbbf24', text: 'Moderate air quality. Acceptable for short periods but lacks the freshness required for peak health.' },
      { label: 'Balanced', max: 75, color: '#10b981', text: 'Stable metrics. Particulates < 15µg/m³ and humidity in the safe 45-55% zone support lung health.' },
      { label: 'Optimal', max: 90, color: '#059669', text: 'Highly restorative air. Low-stress environment with perfect oxygenation to support long-term wellness.' },
      { label: 'Elite', max: 100, color: '#047857', text: 'Museum-grade filtration and total thermal stability. Peak biological safety for the most sensitive occupants.' },
    ],
    getStatus: v => v < 15 ? 'HAZARDOUS' : v < 30 ? 'CRITICAL' : v < 45 ? 'POOR' : v < 60 ? 'FAIR' : v < 75 ? 'BALANCED' : v < 90 ? 'OPTIMAL' : 'ELITE',
  },
  sleep: {
    label: 'SLEEP RECOVERY', id: 'sleep', color: '#8b5cf6', sub: 'Circadian Hygiene',
    ranges: [
      { label: 'Insomnia', max: 15, color: '#f43f5e', text: 'Extreme noise (>60dB) or light (>100 lux). Melatonin production is actively suppressed; sleep is impossible.' },
      { label: 'Restless', max: 30, color: '#e11d48', text: 'Persistent noise/light disruptions. Deep REM and Stage 4 sleep cycles are frequently interrupted.' },
      { label: 'Disturbed', max: 45, color: '#fb923c', text: 'Temperature or humidity spikes causing physical discomfort and night-waking. Recovery is fragmented.' },
      { label: 'Shallow', max: 60, color: '#fbbf24', text: 'Basic rest possible, but background noise or air quality inhibits deep neural restoration.' },
      { label: 'Restful', max: 75, color: '#8b5cf6', text: 'Good environmental quiet (<35dB). Supportive conditions for primary physical and mental recovery.' },
      { label: 'Deep', max: 90, color: '#7c3aed', text: 'Dark (<5 lux) and cool (~18.5°C). Optimal conditions for muscle repair and cognitive memory consolidation.' },
      { label: 'Sublime', max: 100, color: '#6d28d9', text: 'Total sensory isolation. Silent, dark, and perfectly ventilated for maximum growth hormone release.' },
    ],
    getStatus: v => v < 15 ? 'INSOMNIA' : v < 30 ? 'RESTLESS' : v < 45 ? 'DISTURBED' : v < 60 ? 'SHALLOW' : v < 75 ? 'RESTFUL' : v < 90 ? 'DEEP' : 'SUBLIME',
  },
  work: {
    label: 'WORK FOCUS', id: 'work', color: '#0ea5e9', sub: 'Cognitive Throughput',
    ranges: [
      { label: 'Toxic', max: 15, color: '#f43f5e', text: 'High VOC/CO2 proxies detected. Severe "Brain Fog," lethargy, and headaches are certain.' },
      { label: 'Blocked', max: 30, color: '#e11d48', text: 'Extreme environmental stress (noise/heat). Productivity is functionally zero due to sensory overload.' },
      { label: 'Struggling', max: 45, color: '#fb923c', text: 'Low light (<150 lux) and stagnant air causing lethargy. Mental processing speed is significantly lowered.' },
      { label: 'Baseline', max: 60, color: '#fbbf24', text: 'Functional workspace. Minor sensory friction or humidity drift prevents long-term flow states.' },
      { label: 'Focused', max: 75, color: '#0ea5e9', text: 'Task-appropriate lighting (>400 lux) and quiet. Sustained concentration is achievable for complex tasks.' },
      { label: 'Productive', max: 90, color: '#0284c7', text: 'Clean air and stable temperature support high cognitive throughput and sustained mental clarity.' },
      { label: 'Peak Flow', max: 100, color: '#0369a1', text: 'Total cognitive clarity. Zero sensory distractions and perfect oxygenation for maximum flow-state duration.' },
    ],
    getStatus: v => v < 15 ? 'TOXIC' : v < 30 ? 'BLOCKED' : v < 45 ? 'STRUGGLING' : v < 60 ? 'BASELINE' : v < 75 ? 'FOCUSED' : v < 90 ? 'PRODUCTIVE' : 'PEAK FLOW',
  },
  fun: {
    label: 'SOCIAL ATMOSPHERE', id: 'fun', color: '#f43f5e', sub: 'Ambient Energy',
    ranges: [
      { label: 'Sterile', max: 15, color: '#71717a', text: 'Cold, dim, and silent. Environment feels abandoned and uninviting for any human interaction.' },
      { label: 'Dull', max: 30, color: '#a1a1aa', text: 'Lacks ambient energy. Conversation feels strained due to poor acoustics or thermal discomfort.' },
      { label: 'Subdued', max: 45, color: '#fbbf24', text: 'Functional for quiet 1-on-1s, but lacks the energy or vibrancy for group social activities.' },
      { label: 'Casual', max: 60, color: '#10b981', text: 'Pleasant temperature and light. Comfortable for low-energy social engagement and relaxation.' },
      { label: 'Vibrant', max: 75, color: '#f43f5e', text: 'Energizing atmosphere. Warm lighting (>500 lux) and fresh air actively encourage social flow.' },
      { label: 'Electric', max: 90, color: '#e11d48', text: 'Peak hosting energy. Ideal 55-65dB ambient floor and vivid light for maximum group engagement.' },
      { label: 'Luminous', max: 100, color: '#be123c', text: 'Peak sensory engagement. Ideal atmosphere for high-energy social gatherings and vivid interactions.' },
    ],
    getStatus: v => v < 15 ? 'STERILE' : v < 30 ? 'DULL' : v < 45 ? 'SUBDUED' : v < 60 ? 'CASUAL' : v < 75 ? 'VIBRANT' : v < 90 ? 'ELECTRIC' : 'LUMINOUS',
  }
}

const CONVERSIONS = {
  temperature_c: {
    imperial: { unit: '°F', convert: v => (v * 9 / 5) + 32 },
    metric: { unit: '°C', convert: v => v }
  },
  pressure_hpa: {
    imperial: { unit: 'inHg', convert: v => v * 0.02953 },
    metric: { unit: 'hPa', convert: v => v }
  }
}

/* ═══════════════════════════════════════════════════
   CUSTOM VISUALIZATIONS
   ═══════════════════════════════════════════════════ */

const RadarMatrix = ({ scores, activeAxisId, activeColor, onAxisClick }) => {
  const center = 100;
  const radius = 70;
  
  const axes = [
    { ...ACTIVITY_META.health, angle: -90, val: scores?.health ?? 0 },
    { ...ACTIVITY_META.work, angle: 0, val: scores?.work ?? 0 },
    { ...ACTIVITY_META.sleep, angle: 90, val: scores?.sleep ?? 0 },
    { ...ACTIVITY_META.fun, angle: 180, val: scores?.fun ?? 0 }
  ];

  const getCoord = (val, angle) => {
    const rad = angle * (Math.PI / 180);
    const r = (val / 100) * radius;
    return { x: center + r * Math.cos(rad), y: center + r * Math.sin(rad) };
  };

  const points = axes.map(a => `${getCoord(a.val, a.angle).x},${getCoord(a.val, a.angle).y}`).join(' ');

  const hOp = Math.round((scores?.health ?? 0) * 1.0).toString(16).padStart(2, '0');
  const wOp = Math.round((scores?.work ?? 0) * 1.0).toString(16).padStart(2, '0');
  const sOp = Math.round((scores?.sleep ?? 0) * 1.0).toString(16).padStart(2, '0');
  const fOp = Math.round((scores?.fun ?? 0) * 1.0).toString(16).padStart(2, '0');

  const dynamicGradient = `
    radial-gradient(circle at 50% 25%, ${ACTIVITY_META.health.color}${hOp}, transparent 70%),
    radial-gradient(circle at 75% 50%, ${ACTIVITY_META.work.color}${wOp}, transparent 70%),
    radial-gradient(circle at 50% 75%, ${ACTIVITY_META.sleep.color}${sOp}, transparent 70%),
    radial-gradient(circle at 25% 50%, ${ACTIVITY_META.fun.color}${fOp}, transparent 70%)
  `;

  return (
    <div className="relative h-full w-full max-h-full max-w-full aspect-square mx-auto flex items-center justify-center p-8">
      <div 
        className="absolute inset-0 rounded-full animate-hum" 
        style={{ background: dynamicGradient, transition: 'background 1s ease-in-out' }}
      ></div>
      
      <svg viewBox="0 0 200 200" className="w-full h-full overflow-visible relative z-10">
        {[25, 50, 75, 100].map((tier, i) => {
          const pts = axes.map(a => `${getCoord(tier, a.angle).x},${getCoord(tier, a.angle).y}`).join(' ');
          return <polygon key={i} points={pts} fill="none" stroke="#27272a" strokeWidth="1" strokeDasharray={i === 3 ? "none" : "2 4"} />;
        })}
        
        {axes.map((a, i) => {
          const pt = getCoord(100, a.angle);
          return (
            <g key={i} onClick={() => onAxisClick?.(a.id)} className="cursor-pointer group">
              <line x1={center} y1={center} x2={pt.x} y2={pt.y} stroke={a.color} strokeWidth="1" strokeOpacity="0.5" />
              <text 
                x={center + (radius + 24) * Math.cos(a.angle * Math.PI / 180)} 
                y={center + (radius + 24) * Math.sin(a.angle * Math.PI / 180)} 
                fill={a.color} 
                fontSize="11" fontFamily="monospace"
                textAnchor="middle" dominantBaseline="middle"
                className="font-bold transition-all duration-300 group-hover:brightness-150"
                letterSpacing="0.1em"
              >
                {a.id.toUpperCase()}
              </text>
            </g>
          );
        })}

        {/* Per-axis colored triangle segments */}
        {axes.map((a, i) => {
          const nextAxis = axes[(i + 1) % axes.length];
          const pt1 = getCoord(a.val, a.angle);
          const pt2 = getCoord(nextAxis.val, nextAxis.angle);
          return (
            <g key={`seg-${i}`}>
              <polygon
                points={`${center},${center} ${pt1.x},${pt1.y} ${pt2.x},${pt2.y}`}
                fill={`${a.color}20`}
                className="transition-all duration-700 ease-out"
              />
              <line
                x1={pt1.x} y1={pt1.y} x2={pt2.x} y2={pt2.y}
                stroke={a.color} strokeWidth="1.5" strokeOpacity="0.7"
                className="transition-all duration-700 ease-out"
              />
            </g>
          );
        })}

        {axes.map((a, i) => {
          const pt = getCoord(a.val, a.angle);
          return (
            <circle 
              key={i} cx={pt.x} cy={pt.y} r={3} fill={a.color}
              onClick={() => onAxisClick?.(a.id)}
              className="transition-all duration-700 ease-out cursor-pointer hover:r-5"
            />
          );
        })}
      </svg>
    </div>
  );
};

const AreaChart = ({ history, sensorKey, color, unitSystem, isExpanded }) => {
  const [hoverIdx, setHoverIdx] = useState(null);
  const containerRef = useRef(null);

  const data = history.map(entry => {
    let val = entry[sensorKey];
    if (val == null) return 0;
    const conv = CONVERSIONS[sensorKey]?.[unitSystem];
    return conv ? conv.convert(val) : val;
  });

  if (data.length === 0) return null;

  const baseRanges = {
    temperature_c: 0.5,
    humidity_pct: 1,
    light_lux: 10,
    noise_db: 8,
    pressure_hpa: 0.5,
    pm25_ugm3: 1
  };
  
  let minRangeVal = baseRanges[sensorKey] || 5;
  const rangeConv = CONVERSIONS[sensorKey]?.[unitSystem];
  if (rangeConv) {
    minRangeVal = Math.abs(rangeConv.convert(minRangeVal) - rangeConv.convert(0));
  }

  let min = Math.min(...data);
  let max = Math.max(...data);
  let range = max - min;

  // Enforce a minimum scale range relative to each metric
  if (range < minRangeVal) {
    const center = (max + min) / 2 || 0;
    min = center - (minRangeVal / 2);
    max = center + (minRangeVal / 2);
    range = minRangeVal;
  }

  const getXY = (val, i) => {
    const x = (i / Math.max(data.length - 1, 1)) * 100;
    const y = 100 - (((val - min) / range) * 90 + 5);
    return [x, y];
  };

  let pathD = `M ${getXY(data[0], 0).join(',')}`;
  for (let i = 0; i < data.length - 1; i++) {
    const [x0, y0] = getXY(data[i], i);
    const [x1, y1] = getXY(data[i + 1], i + 1);
    const cx1 = x0 + (x1 - x0) * 0.15;
    const cx2 = x1 - (x1 - x0) * 0.15;
    pathD += ` C ${cx1},${y0} ${cx2},${y1} ${x1},${y1}`;
  }

  const areaD = `${pathD} L 100,100 L 0,100 Z`;

  const handleMouseMove = (e) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const pct = x / rect.width;
    const idx = Math.round(pct * (data.length - 1));
    setHoverIdx(Math.max(0, Math.min(data.length - 1, idx)));
  };

  const hoverPoint = hoverIdx !== null ? getXY(data[hoverIdx], hoverIdx) : null;

  return (
    <div 
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => setHoverIdx(null)}
      className="w-full h-full relative cursor-crosshair group/chart"
    >
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="w-full h-full overflow-visible">
        <defs>
          <linearGradient id={`grad-${sensorKey}`} x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.4" />
            <stop offset="100%" stopColor={color} stopOpacity="0.0" />
          </linearGradient>
        </defs>
        <path d="M0,25 L100,25 M0,50 L100,50 M0,75 L100,75" stroke="#27272a" strokeWidth="0.5" fill="none" />
        <path d={areaD} fill={`url(#grad-${sensorKey})`} style={{ transition: 'all 500ms linear' }} />
        <path d={pathD} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" style={{ transition: 'all 500ms linear' }} />
        
        {hoverPoint && (
          <line x1={hoverPoint[0]} y1="0" x2={hoverPoint[0]} y2="100" stroke={color} strokeWidth="0.5" strokeDasharray="2 1" strokeOpacity="0.5" />
        )}
      </svg>

      {isExpanded && [25, 50, 75].map(yPct => {
        const val = min + (((100 - yPct) - 5) / 90) * range;
        const unit = CONVERSIONS[sensorKey]?.[unitSystem]?.unit || SENSOR_META[sensorKey]?.unit;
        return (
          <div 
            key={yPct} 
            className="absolute left-2 text-[9px] font-mono text-zinc-600 uppercase pointer-events-none"
            style={{ top: `${yPct}%`, transform: 'translateY(-100%)' }}
          >
            {val.toFixed(1)}{unit}
          </div>
        );
      })}

      {hoverPoint && (
        <div 
          className="absolute z-40 pointer-events-none rounded-full border-2 border-white shadow-[0_0_10px_rgba(0,0,0,0.8)] transition-all duration-75"
          style={{ 
            left: `${hoverPoint[0]}%`, 
            top: `${hoverPoint[1]}%`,
            width: '8px',
            height: '8px',
            backgroundColor: color,
            transform: 'translate(-50%, -50%)',
            boxShadow: `0 0 12px ${color}`
          }}
        />
      )}

      {hoverIdx !== null && (
        <div 
          className="absolute z-50 pointer-events-none bg-zinc-900/95 border border-zinc-700 px-3 py-2 rounded-md shadow-2xl text-[11px] font-mono whitespace-nowrap animate-in fade-in zoom-in duration-150 backdrop-blur-md"
          style={{ 
            left: `${Math.min(80, Math.max(20, hoverPoint[0]))}%`, 
            top: '5%',
            transform: 'translateX(-50%)'
          }}
        >
          <div className="flex flex-col gap-1">
            <span className="text-zinc-500 text-[9px] uppercase tracking-wider border-b border-zinc-800 pb-1 mb-1">
              {history[hoverIdx]?.timestamp ? new Date(history[hoverIdx].timestamp * 1000).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '---'}
            </span>
            <span className="font-bold text-base text-white flex items-baseline gap-1">
              {data[hoverIdx].toFixed(1)} <span className="text-xs text-zinc-400 font-normal">{CONVERSIONS[sensorKey]?.[unitSystem]?.unit || SENSOR_META[sensorKey]?.unit}</span>
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

function AnimatedNumber({ value, decimals = 1 }) {
  const [displayed, setDisplayed] = useState(value)
  const prevRef = useRef(value)
  const frameRef = useRef(null)

  useEffect(() => {
    const from = prevRef.current
    const to = typeof value === 'number' ? value : parseFloat(value)
    if (isNaN(to)) { setDisplayed(value); return }
    prevRef.current = to
    const duration = 600
    const start = performance.now()
    const animate = (now) => {
      const elapsed = now - start
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3) 
      setDisplayed((from + (to - from) * eased).toFixed(decimals))
      if (progress < 1) frameRef.current = requestAnimationFrame(animate)
    }
    frameRef.current = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(frameRef.current)
  }, [value, decimals])

  return <>{displayed}</>
}

const ResizeHandle = ({ direction = 'horizontal' }) => (
  <PanelResizeHandle
    style={direction === 'vertical' ? { height: '2px', minHeight: '2px', flexShrink: 0 } : { width: '2px', minWidth: '2px', flexShrink: 0 }}
    className={`group z-40 transition-colors duration-200 ${
      direction === 'horizontal'
        ? 'cursor-col-resize bg-zinc-800 hover:bg-zinc-600 active:bg-emerald-500/60'
        : 'cursor-row-resize bg-zinc-800 hover:bg-zinc-600 active:bg-emerald-500/60'
    }`}
  />
);

/* ═══════════════════════════════════════════════════
   MAIN APPLICATION
   ═══════════════════════════════════════════════════ */

export default function App() {
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)
  const [lastFetch, setLastFetch] = useState(null)
  const [history, setHistory] = useState([])
  const [scenarios, setScenarios] = useState([])
  const [manualScenarioId, setManualScenarioId] = useState(null)
  const [analysis, setAnalysis] = useState({ summary: '', flags: [] })
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [analysisError, setAnalysisError] = useState(null)
  const [analysisCooldown, setAnalysisCooldown] = useState(0)

  const [activeSensorKey, setActiveSensorKey] = useState('activity_fun')
  const [activeMonitorId, setActiveMonitorId] = useState('simulation')
  const [monitorsList, setMonitorsList] = useState([])
  const [isTechOpen, setIsTechOpen] = useState(false)
  const [unitSystem, setUnitSystem] = useState('imperial')
  const [isScannerOpen, setIsScannerOpen] = useState(false)
  const [isPairingOpen, setIsPairingOpen] = useState(false)
  const [expandedSensorKey, setExpandedSensorKey] = useState(null)
  const prevActiveSensorKeyRef = useRef('activity_fun')
  
  // Local edit state for room context
  const [isEditingRoomType, setIsEditingRoomType] = useState(false)
  const [newObjectInput, setNewObjectInput] = useState('')

  const [serverActive, setServerActive] = useState(false)
  const [dataActive, setDataActive] = useState(false)
  const lastDataTimestamp = useRef(0)

  /* ── Data Fetching ── */
  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/current-status?device_id=${activeMonitorId}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      
      // Heartbeat flicker (Server)
      setServerActive(true)
      setTimeout(() => setServerActive(false), 100)

      setStatus(data)
      if (data.reading) {
        // Data flicker (Stream) - only if timestamp changed
        if (data.reading.timestamp_ms !== lastDataTimestamp.current) {
          setDataActive(true)
          setTimeout(() => setDataActive(false), 100)
          lastDataTimestamp.current = data.reading.timestamp_ms
        }
        setHistory(prev => {
          const entry = {
            ...data.reading,
            timestamp: data.reading.timestamp_ms || Date.now(),
            health: data.score, sleep: data.sleep_score,
            work: data.work_score, fun: data.fun_score,
          }
          return [...prev, entry].slice(-30)
        })
      }
      setError(null)
      setLastFetch(new Date())
    } catch (err) {
      setError(`Unable to reach backend: ${err.message}`)
    }
  }, [activeMonitorId])

  const fetchMonitors = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/monitors`)
      if (!res.ok) return
      const data = await res.json()
      setMonitorsList(data)
      
      // Auto-select first Live monitor if currently on simulation AND no active preset
      if (activeMonitorId === 'simulation' && (!manualScenarioId || manualScenarioId === 'live')) {
        const firstLive = data.find(m => m.id !== 'simulation')
        if (firstLive) {
          setActiveMonitorId(firstLive.id)
          console.log(`🔌 Auto-switched to Live Monitor: ${firstLive.name}`)
        }
      }
    } catch (err) { console.error(err) }
  }, [activeMonitorId, manualScenarioId])

  const fetchScenarios = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/scenarios`)
      if (res.ok) {
        const data = await res.json()
        setScenarios(data)
      }
    } catch (err) { console.error(err) }
  }, [])

  const selectScenario = async (id, overrideMonitorId = null) => {
    try {
      setManualScenarioId(id)
      
      if (id === 'live') {
        if (overrideMonitorId) {
          setActiveMonitorId(overrideMonitorId);
        } else {
          const firstLive = monitorsList.find(m => m.id !== 'simulation');
          if (firstLive) setActiveMonitorId(firstLive.id);
        }
      } else {
        setActiveMonitorId('simulation');
      }

      await fetch(`${API_BASE}/api/scenarios/select`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id }),
      })
      fetchStatus()
    } catch (err) { }
  }

  const fetchAnalysis = useCallback(async () => {
    if (analysisCooldown > 0) return
    setAnalysisLoading(true)
    setAnalysisError(null)
    try {
      const res = await fetch(`${API_BASE}/api/analyze?device_id=${activeMonitorId}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setAnalysis(await res.json())
      
      // Start 15s cooldown
      setAnalysisCooldown(15)
    } catch (err) {
      setAnalysisError(err.message)
    } finally {
      setAnalysisLoading(false)
    }
  }, [analysisCooldown, activeMonitorId])

  useEffect(() => {
    if (analysisCooldown > 0) {
      const timer = setInterval(() => setAnalysisCooldown(c => c - 1), 1000)
      return () => clearInterval(timer)
    }
  }, [analysisCooldown])

  const saveContextChange = async (updatedType, updatedObjects) => {
    try {
      await fetch(`${API_BASE}/api/room-context/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          device_id: activeMonitorId,
          room_type: updatedType,
          identified_objects: updatedObjects
        })
      });
      fetchStatus();
      // Re-trigger analysis with new context
      setTimeout(fetchAnalysis, 500);
    } catch (err) { console.error(err); }
  }

  const removeObject = (idx) => {
    const next = status.room_context.identified_objects.filter((_, i) => i !== idx);
    saveContextChange(status.room_context.room_type, next);
  }

  const addObject = () => {
    if (!newObjectInput.trim()) return;
    const next = [...(status.room_context.identified_objects || []), newObjectInput.trim()];
    saveContextChange(status.room_context.room_type, next);
    setNewObjectInput('');
  }

  const updateRoomType = (newType) => {
    saveContextChange(newType, status.room_context.identified_objects);
    setIsEditingRoomType(false);
  }

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlDevId = params.get('device_id');
    if (urlDevId) setActiveMonitorId(urlDevId);
    
    if (params.get('scanner') === 'true') {
      setIsScannerOpen(true);
      window.history.replaceState({}, '', window.location.pathname);
    }
    fetchStatus()
    fetchScenarios()
    fetchMonitors()
    const statusInterval = setInterval(fetchStatus, POLL_INTERVAL_MS)
    const monitorInterval = setInterval(fetchMonitors, 5000)
    const scenarioInterval = setInterval(() => {
      if (scenarios.length === 0) fetchScenarios()
    }, 5000)
    return () => {
      clearInterval(statusInterval)
      clearInterval(monitorInterval)
      clearInterval(scenarioInterval)
    }
  }, [fetchStatus, fetchScenarios, fetchMonitors])

  // Auto-close pairing modal when connection or sync is established
  useEffect(() => {
    if (isPairingOpen && (status?.pairing_status === 'connected' || status?.pairing_status === 'finished')) {
      setIsPairingOpen(false);
    }
  }, [status?.pairing_status, isPairingOpen]);

  const reading = status?.reading ?? null
  const connected = status?.connected ?? false
  const isDataStale = connected && reading && (Date.now() - (reading.timestamp_ms || 0) > 5000);

  // Determine Active Focus Logic for UI Highlighting
  const rawKey = activeSensorKey || 'activity_fun'
  const isActivity = rawKey.startsWith('activity_')
  const lookupKey = isActivity ? rawKey.replace('activity_', '') : rawKey
  const activeMeta = isActivity ? ACTIVITY_META[lookupKey] : SENSOR_META[rawKey]
  const activeColor = activeMeta?.color || activeMeta?.iconColor || '#3f3f46'

  // ── Auto-trigger Analysis on Context Sync ──
  const prevPairingStatus = useRef('ready')
  useEffect(() => {
    if (status?.pairing_status === 'completed' && prevPairingStatus.current !== 'completed') {
      // Transition: Just finished on phone!
      fetchAnalysis()
    }
    prevPairingStatus.current = status?.pairing_status
  }, [status?.pairing_status, fetchAnalysis])

  const resetPairing = async () => {
    try {
      await fetch(`${API_BASE}/api/pairing/reset`, { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ device_id: activeMonitorId }), 
      })
      setAnalysis({ summary: '', flags: [] })
      fetchStatus()
    } catch(err) {}
  }

  // Values for the right panel
  const currentActiveValue = isActivity
    ? (status?.[lookupKey === 'health' ? 'score' : `${lookupKey}_score`] ?? null)
    : (reading?.[rawKey] ?? null)
  
  const displayActiveValue = currentActiveValue != null 
    ? (isActivity ? Math.round(currentActiveValue) : (() => {
        const conv = CONVERSIONS[rawKey]?.[unitSystem];
        const v = conv ? conv.convert(currentActiveValue) : currentActiveValue;
        return v.toFixed(1);
      })()) 
    : '--'

  const scoreData = {
    health: status?.score ?? 0,
    work: status?.work_score ?? 0,
    sleep: status?.sleep_score ?? 0,
    fun: status?.fun_score ?? 0
  }

  /* ═══════════════════════════════════════════════════
     RENDER
     ═══════════════════════════════════════════════════ */

  // If accessed via #scan hash (mobile phone from QR code), show only the scanner
  if (window.location.hash === '#scan') {
    const params = new URLSearchParams(window.location.search);
    const mobileDevId = params.get('device_id') || 'simulation';
    return (
      <div className="h-screen w-full bg-[#09090b]">
        <RoomScanner 
          deviceId={mobileDevId}
          onClose={() => { window.location.hash = ''; window.location.reload(); }} 
        />
      </div>
    )
  }

  return (
    <div className="h-screen w-full bg-[#09090b] text-zinc-300 font-sans flex flex-col overflow-hidden selection:bg-zinc-800">
      
      {/* ──────────── HEADER ──────────── */}
      <header className="h-12 flex items-center justify-between px-4 border-b border-zinc-800/80 bg-[#09090b] shrink-0 z-10">
        <div className="flex items-center gap-6 h-full">
          <div className="flex items-center gap-3 border-r border-zinc-800/80 pr-6 h-full">
            <div className="w-5 h-5 rounded overflow-hidden flex items-center justify-center bg-zinc-900 border border-zinc-800">
              <img src="/airvita-brand.png" alt="AirVita Logo" className="w-full h-full object-cover invert opacity-90" />
            </div>
            <span className="font-bold text-sm tracking-widest text-zinc-100 uppercase">AirVita</span>
          </div>
          
          <div className="hidden sm:flex items-center gap-8 font-mono text-[10px] uppercase tracking-[0.15em]">
            <div className="flex items-center gap-3">
              <div className={`w-8 h-8 rounded-sm transition-all duration-500 flex items-center justify-center shrink-0 ${connected ? (serverActive ? 'bg-emerald-500/15 border-emerald-500/30' : 'bg-emerald-500/10 border-emerald-500/20') : 'animate-danger'}`}>
                <Radio size={14} className={`transition-colors duration-300 ${connected ? (serverActive ? "text-emerald-400" : "text-emerald-500/50") : "text-rose-500"}`} />
              </div>
              <div className="flex flex-col justify-center">
                <span className="text-[11px] text-zinc-200 font-bold leading-none mb-1">Server Status</span>
                <span className={`text-[9px] transition-colors duration-500 ${connected ? (serverActive ? 'text-emerald-400' : 'text-emerald-500/50') : 'text-rose-500 font-bold'} leading-none`}>
                  {connected ? 'CONNECTED' : 'OFFLINE'}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className={`w-8 h-8 rounded-sm transition-all duration-500 flex items-center justify-center shrink-0 ${!isDataStale && connected ? (dataActive ? 'bg-emerald-500/15 border-emerald-500/30' : 'bg-emerald-500/10 border-emerald-500/20') : 'animate-danger'}`}>
                <Activity size={14} className={`transition-colors duration-300 ${!isDataStale && connected ? (dataActive ? "text-emerald-400" : "text-emerald-500/50") : "text-rose-500"}`} />
              </div>
              <div className="flex flex-col justify-center">
                <span className="text-[11px] text-zinc-200 font-bold leading-none mb-1">Data Stream</span>
                <span className={`text-[9px] transition-colors duration-500 ${!isDataStale && connected ? (dataActive ? 'text-emerald-400' : 'text-emerald-500/50') : 'text-rose-500 font-bold'} leading-none`}>
                  {!isDataStale && connected ? 'ACTIVE' : 'DROPPED'}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center h-full gap-4">


          <select
            value={activeMonitorId === 'simulation' ? '' : activeMonitorId}
            onChange={e => {
              const newId = e.target.value;
              if (activeMonitorId === 'simulation') {
                selectScenario('live', newId);
              } else {
                setActiveMonitorId(newId);
              }
            }}
            className="bg-zinc-900 border border-zinc-700 text-zinc-200 text-xs font-mono uppercase tracking-widest rounded px-3 py-1.5 outline-none cursor-pointer focus:border-emerald-500 focus:bg-zinc-800"
          >
            {activeMonitorId === 'simulation' && (
              <option value="" disabled className="bg-zinc-900 text-zinc-500">
                -- SIMULATION ACTIVE --
              </option>
            )}
            {monitorsList.filter(m => m.id !== 'simulation').map(m => (
              <option key={m.id} value={m.id} className="bg-zinc-900 text-zinc-200">
                {m.connected ? '●' : '○'} {m.name}
              </option>
            ))}
          </select>

          <select
            value={manualScenarioId || (activeMonitorId === 'simulation' ? 'simulation' : 'live')}
            onChange={e => selectScenario(e.target.value)}
            className="hidden md:block bg-zinc-900 border border-zinc-700 text-zinc-200 text-xs font-mono uppercase tracking-widest rounded px-3 py-1.5 outline-none cursor-pointer focus:border-zinc-500 focus:bg-zinc-800"
          >
            <option value="live" className="bg-zinc-900 text-zinc-200">Mode: Hardware</option>
            {scenarios.map(s => <option key={s.id} value={s.id} className="bg-zinc-900 text-zinc-200">Simulation: {s.name}</option>)}
          </select>

          <div className="flex items-center border-l border-zinc-800/80 h-full pl-4 gap-4">
            <button onClick={() => setIsTechOpen(!isTechOpen)} className="text-zinc-500 hover:text-zinc-300">
              <Settings2 size={16} />
            </button>
          </div>
        </div>
      </header>

      {/* ──────────── MAIN: Two Horizontal Bands ──────────── */}
      <main className="flex-1 min-h-0 flex flex-col">
        <PanelGroup direction="vertical">
          <Panel defaultSize={48} minSize={30}>
            <PanelGroup direction="horizontal">
              {/* ── Radar Matrix ── */}
              <Panel defaultSize={30} minSize={20}>
                <div className="h-full relative flex items-center justify-center bg-zinc-950/30 p-6 overflow-hidden">
                  <RadarMatrix scores={scoreData} activeAxisId={isActivity ? lookupKey : null} activeColor={activeColor} onAxisClick={(id) => setActiveSensorKey('activity_' + id)} />
                </div>
              </Panel>

              <ResizeHandle />

              {/* ── Current Focus — Threshold Details ── */}
              <Panel defaultSize={35} minSize={25}>
                <div className="h-full flex flex-col bg-[#09090b]">
                  {/* Focus Header */}
                  <div className="px-5 py-4 flex items-center justify-between bg-zinc-900/20 border-b border-zinc-800/50 shrink-0">
                    <span className="text-base font-mono text-zinc-400 uppercase tracking-widest">
                      Focus: <span className="font-semibold transition-colors duration-500" style={{ color: activeColor }}>{activeMeta?.label || activeMeta?.shortLabel || 'SYSTEM'}</span>
                    </span>
                    <span className="text-base font-mono font-semibold transition-colors duration-500" style={{ color: activeColor }}>
                      [{displayActiveValue} {isActivity ? 'PTS' : (CONVERSIONS[rawKey]?.[unitSystem]?.unit || activeMeta?.unit)}]
                    </span>
                  </div>

                  {activeSensorKey === 'pm25_ugm3' && (
                    <div className="px-5 py-3 border-b border-zinc-800/50 flex gap-6 text-[11px] font-mono text-zinc-500 uppercase bg-zinc-900/10">
                      <div className="flex flex-col gap-1">
                        <span className="text-[9px] text-zinc-600">Fine (&gt;0.3µ)</span>
                        <span className="text-zinc-200">{reading?.pc_0_3 ?? '--'}</span>
                      </div>
                      <div className="flex flex-col gap-1">
                        <span className="text-[9px] text-zinc-600">Small (&gt;0.5µ)</span>
                        <span className="text-zinc-200">{reading?.pc_0_5 ?? '--'}</span>
                      </div>
                      <div className="flex flex-col gap-1">
                        <span className="text-[9px] text-zinc-600">Large (&gt;1.0µ)</span>
                        <span className="text-zinc-200">{reading?.pc_1_0 ?? '--'}</span>
                      </div>
                    </div>
                  )}

                  {/* Threshold Tiers — vertical list with more room */}
                  <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-3">
                    {activeMeta?.ranges.map((t, idx) => {
                      let isActiveRange = false;
                      if (currentActiveValue != null) {
                        const prevMax = idx > 0 ? activeMeta.ranges[idx - 1].max : -Infinity;
                        isActiveRange = currentActiveValue > prevMax && currentActiveValue <= t.max;
                      }
                      return (
                        <div key={idx} className="group flex flex-col gap-2 mb-3">
                          <div className="flex items-center justify-between">
                            <span 
                              className={`text-base font-mono uppercase tracking-widest transition-colors ${isActiveRange ? 'font-semibold' : 'text-zinc-600 group-hover:text-zinc-500'}`}
                              style={isActiveRange ? { color: activeColor } : {}}
                            >
                              {t.label}
                            </span>
                            <span className="text-sm font-mono text-zinc-600">≤ {t.max}</span>
                          </div>
                          <p className={`text-base leading-snug transition-colors duration-300 ${isActiveRange ? 'text-zinc-300' : 'text-zinc-600'}`}>
                            {t.text}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </Panel>

              <ResizeHandle />

              {/* ── AI Insights / Scanner ── */}
              <Panel defaultSize={35} minSize={25}>
                <div className="h-full flex flex-col bg-[#09090b] min-h-0">
                  {/* Header */}
                  <div className="px-4 py-3 border-b border-zinc-800/80 flex items-center justify-between shrink-0 bg-zinc-900/20">
                    <span className="text-sm font-mono uppercase tracking-widest flex items-center gap-2 transition-colors duration-500" style={{ color: activeColor }}>
                      <BrainCircuit size={16} /> Neural Diagnostics
                    </span>
                    <div className="flex items-center gap-3">
                      {analysisCooldown > 0 && (
                        <span className="text-xs font-mono text-zinc-600 uppercase">COOLDOWN: {analysisCooldown}S</span>
                      )}
                      <button 
                        onClick={fetchAnalysis} 
                        disabled={analysisLoading || analysisCooldown > 0} 
                        className={`transition-colors ${(analysisLoading || analysisCooldown > 0) ? 'text-zinc-800' : 'text-zinc-600 hover:text-zinc-300'}`}
                      >
                        <RefreshCw size={16} className={analysisLoading ? 'animate-spin' : ''} />
                      </button>
                    </div>
                  </div>

                   {/* Scanning Visualizer */}
                  <div className="min-h-[112px] h-auto border-b border-zinc-800/80 bg-zinc-950 relative flex items-center justify-center group py-6">
                    <div className="absolute inset-0" style={{ backgroundImage: 'linear-gradient(#18181b 1px, transparent 1px), linear-gradient(90deg, #18181b 1px, transparent 1px)', backgroundSize: '12px 12px' }}></div>
                    
                    {(analysisLoading || (status?.pairing_status === 'connected' && !status?.room_context?.room_type)) && (
                      <div className="absolute top-0 left-0 right-0 h-0.5 opacity-50 animate-[scan_3s_ease-in-out_infinite] transition-colors duration-500" style={{ backgroundColor: activeColor, boxShadow: `0 0 8px ${activeColor}` }}></div>
                    )}
                    
                    <div className="relative z-10 text-center px-4 w-full">
                      {analysisError ? (
                        <>
                          <AlertCircle size={20} className="mx-auto text-[#f43f5e] mb-1" />
                          <span className="text-xs font-mono text-[#f43f5e] uppercase tracking-widest block">{analysisError}</span>
                        </>
                      ) : (status?.pairing_status === 'finished' || status?.room_context?.room_type) ? (
                        <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-4 px-6 w-full">
                          <div className="flex items-center gap-4">
                             <CheckCircle2 size={28} className="text-emerald-500 shrink-0" />
                             <div className="flex flex-col">
                               <span className="text-lg font-mono uppercase tracking-[0.2em] text-emerald-500 font-bold leading-none mb-1">SCAN RECEIVED</span>
                               <div className="text-[11px] font-mono text-zinc-400 uppercase tracking-widest flex items-center gap-2">
                                  Context: 
                                  {isEditingRoomType ? (
                                    <input 
                                      autoFocus
                                      className="bg-zinc-900 border border-zinc-700 text-zinc-100 px-2 py-0.5 outline-none rounded"
                                      defaultValue={status?.room_context?.room_type}
                                      onBlur={(e) => updateRoomType(e.target.value)}
                                      onKeyDown={(e) => e.key === 'Enter' && updateRoomType(e.target.value)}
                                    />
                                  ) : (
                                    <span 
                                      className="text-zinc-200 cursor-pointer hover:text-white border-b border-dashed border-zinc-700"
                                      onClick={() => setIsEditingRoomType(true)}
                                    >
                                      {status?.room_context?.room_type || 'UNDEFINED'}
                                    </span>
                                  )}
                               </div>
                             </div>
                          </div>
                          
                          <div className="flex flex-wrap gap-2 flex-1 justify-center min-w-[200px]">
                            {status?.room_context?.identified_objects?.length > 0 && (
                              <>
                                {status.room_context.identified_objects.map((obj, i) => (
                                  <span key={i} className="group/tag relative text-[10px] font-mono bg-zinc-800/50 text-zinc-300 px-2 py-1 rounded uppercase border border-zinc-700/30 flex items-center gap-1.5 whitespace-nowrap">
                                    {obj}
                                    <button 
                                      onClick={() => removeObject(i)}
                                      className="text-zinc-600 hover:text-rose-400 transition-colors ml-0.5 text-xs"
                                    >
                                      ×
                                    </button>
                                  </span>
                                ))}
                                <div className="flex items-center ml-2">
                                  <input 
                                    placeholder="+ ITEM"
                                    className="bg-transparent border-b border-zinc-800 text-[10px] font-mono w-16 outline-none text-zinc-500 focus:text-zinc-300 transition-colors"
                                    value={newObjectInput}
                                    onChange={(e) => setNewObjectInput(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && addObject()}
                                  />
                                </div>
                              </>
                            )}
                          </div>
                          
                          <button 
                            onClick={() => {
                              resetPairing();
                              setIsPairingOpen(true);
                            }} 
                            className="text-[10px] font-mono text-zinc-500 hover:text-zinc-300 uppercase underline decoration-zinc-800 underline-offset-4 shrink-0"
                          >
                            Rescan Room
                          </button>
                        </div>
                      ) : status?.pairing_status === 'connected' ? (
                        <div className="flex items-center gap-6 px-6">
                          <Radio size={32} className="text-blue-500 animate-pulse shrink-0" />
                          <div className="flex flex-col text-left">
                            <span className="text-sm font-mono text-blue-400 uppercase tracking-widest block font-bold">Device Link Established</span>
                            <span className="text-xs font-mono text-zinc-500 block mt-0.5 uppercase">Continue scanning on your phone...</span>
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-center gap-6 px-6">
                          <Camera size={32} className="text-zinc-600 transition-colors duration-500 group-hover:text-zinc-400 shrink-0" />
                          <div className="flex flex-col text-left">
                            <span className="text-base font-mono text-zinc-500 uppercase tracking-widest block">Awaiting Mobile Link</span>
                            <button onClick={() => setIsPairingOpen(true)} className="text-xs font-mono text-zinc-400 underline mt-1 hover:text-zinc-200 text-left">Initialize Scanner</button>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* System Summary */}
                  <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
                    <span className="text-sm font-mono text-zinc-500 uppercase tracking-widest mb-4 block">AI Analysis</span>
                    <p className="text-lg text-zinc-300 leading-relaxed font-sans tracking-tight mb-5">
                      <span className="font-mono mr-2 transition-colors duration-500" style={{ color: activeColor }}>{'>'}</span>
                      {analysis.summary || "Run analysis to process environmental payload against neural matrix."}
                    </p>
                    {analysis.flags?.length > 0 && (
                      <div className="pt-5 border-t border-zinc-800/50 space-y-3">
                        {analysis.flags.map((flag, i) => (
                          <div key={i} className="text-base font-mono text-zinc-400">
                            <span className="text-zinc-600 mr-2">−</span> {typeof flag === 'string' ? flag : flag.message || flag.label || JSON.stringify(flag)}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </Panel>
            </PanelGroup>
          </Panel>

          <ResizeHandle direction="vertical" />

          <Panel defaultSize={52} minSize={20}>
            <div className="h-full flex flex-col min-h-0 bg-zinc-950">
              <div className="flex-1 grid grid-cols-12 grid-flow-dense gap-[2px] bg-zinc-800 overflow-hidden">
                    {Object.keys(SENSOR_META).map((key, idx) => {
                      const meta = SENSOR_META[key];
                      const isActive = activeSensorKey === key;
                      const isExpanded = expandedSensorKey === key;
                      const rawVal = reading?.[key];
                      const numericVal = rawVal != null ? (CONVERSIONS[key]?.[unitSystem]?.convert(rawVal) ?? rawVal) : null;
                      
                      return (
                        <motion.div 
                          layout
                          transition={{
                            layout: { type: 'spring', damping: 25, stiffness: 120 }
                          }}
                          key={key} 
                          onClick={() => {
                            if (isExpanded) {
                              setExpandedSensorKey(null);
                              setActiveSensorKey(prevActiveSensorKeyRef.current);
                            } else {
                              prevActiveSensorKeyRef.current = activeSensorKey;
                              setActiveSensorKey(key);
                              setExpandedSensorKey(key);
                            }
                          }}
                          className={`relative bg-[#09090b] p-4 flex flex-col group overflow-hidden cursor-pointer border border-transparent hover:border-zinc-800 ${
                            isExpanded ? 'col-span-12 md:col-span-8 row-span-2 shadow-2xl z-30 order-first' : 'col-span-4 order-none'
                          } ${isActive && !isExpanded ? 'bg-zinc-900/40' : ''}`}
                        >
                          <div className="absolute inset-0 opacity-0 group-hover:opacity-10 transition-opacity duration-500 pointer-events-none" style={{ background: `radial-gradient(circle at top right, ${meta.iconColor}, transparent 70%)` }}></div>
                          {isActive && <div className="absolute top-0 left-0 right-0 h-[1px]" style={{ backgroundColor: meta.iconColor, boxShadow: `0 0 8px ${meta.iconColor}`}}></div>}
                          
                          <div className="flex justify-between items-start z-10 shrink-0">
                            <div className="flex items-center gap-2">
                              <meta.icon size={16} style={{ color: isActive ? meta.iconColor : '#71717a' }} />
                              <span className={`text-xs xl:text-sm font-mono tracking-widest ${isActive ? 'text-zinc-200' : 'text-zinc-400'}`}>{meta.shortLabel}</span>
                            </div>
                            <div className="flex items-center gap-3">
                               <span className={`text-[11px] xl:text-xs font-mono px-2 py-0.5 rounded-sm border ${isActive ? 'border-zinc-600 text-zinc-300' : 'border-zinc-800 text-zinc-600'}`}>{rawVal != null ? meta.getStatus(rawVal) : 'OFF'}</span>
                            </div>
                          </div>
                          
                          <div className="flex items-baseline gap-1 mt-3 z-10 shrink-0">
                            <span className={`text-4xl xl:text-5xl font-light tracking-tighter transition-all duration-500 ${isExpanded ? 'text-5xl xl:text-7xl' : ''} ${isActive ? 'text-white' : 'text-zinc-300'}`}>
                              {numericVal != null ? <AnimatedNumber value={numericVal} decimals={1} /> : '--'}
                            </span>
                            <span className="text-sm xl:text-base font-mono text-zinc-500">{CONVERSIONS[key]?.[unitSystem]?.unit || meta.unit}</span>
                          </div>
                        {key === 'pm25_ugm3' && (
                          <div className="absolute bottom-1.5 right-4 flex gap-1.5 text-[8px] xl:text-[9px] font-mono text-zinc-500 uppercase z-20 bg-zinc-950/90 px-2 py-0.5 rounded-sm border border-zinc-800/80">
                             <span className="text-zinc-400 font-bold tracking-widest">PART:</span>
                             <span>0.3µ:{reading?.pc_0_3 ?? '--'}</span>
                             <span className="text-zinc-800">|</span>
                             <span>0.5µ:{reading?.pc_0_5 ?? '--'}</span>
                             <span className="text-zinc-800">|</span>
                             <span>1.0µ:{reading?.pc_1_0 ?? '--'}</span>
                          </div>
                        )}
                        <div className="flex-1 min-h-0 pt-1 z-10 pr-2">
                          <AreaChart 
                            history={history} 
                            sensorKey={key} 
                            color={meta.iconColor} 
                            unitSystem={unitSystem} 
                            isExpanded={isExpanded}
                          />
                        </div>
                      </motion.div>
                    )
                  })}
              </div>
            </div>
          </Panel>
        </PanelGroup>
      </main>

      {/* ──────────── SETTINGS DRAWER ──────────── */}
      {isTechOpen && (
        <>
          <div onClick={() => setIsTechOpen(false)} className="fixed inset-0 z-40 bg-[#09090b]/60 backdrop-blur-sm" />
          <aside className="fixed top-0 left-0 bottom-0 z-50 w-full max-w-[380px] bg-[#09090b] border-r border-zinc-800 shadow-2xl p-6 flex flex-col overflow-y-auto custom-scrollbar animate-[slideIn_0.2s_ease-out]">
            <div className="flex items-center justify-between mb-8 border-b border-zinc-800 pb-4">
              <div className="flex items-center gap-3">
                <Settings2 className="text-zinc-500" size={18}/>
                <h3 className="text-sm font-mono uppercase tracking-widest text-zinc-100 m-0">Settings</h3>
              </div>
              <button onClick={() => setIsTechOpen(false)} className="text-zinc-500 hover:text-zinc-300 transition-colors">
                <X size={20} />
              </button>
            </div>

            <div className="mb-8">
              <h4 className="text-xs font-mono uppercase tracking-widest text-zinc-500 mb-4">System Status</h4>
              <div className="bg-zinc-900/50 rounded border border-zinc-800 p-4 space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] font-mono text-zinc-500 uppercase">Last Data Sync</span>
                  <span className="text-[10px] font-mono text-zinc-300">{lastFetch ? lastFetch.toLocaleTimeString() : '---'}</span>
                </div>
                <div className="flex justify-between items-center pt-3 border-t border-zinc-800/50">
                   <span className="text-[10px] font-mono text-zinc-500 uppercase">Active Source</span>
                   <span className="text-[10px] font-mono text-zinc-300 uppercase tracking-wider">[{activeMonitorId === 'simulation' ? 'SIMULATOR' : 'HARDWARE'}]</span>
                </div>
              </div>
            </div>

            <div className="mb-8">
              <h4 className="text-xs font-mono uppercase tracking-widest text-zinc-500 mb-4">Preferences</h4>
              <div className="flex items-center justify-between p-3 rounded border border-zinc-800 bg-zinc-900/50">
                <span className="text-xs font-mono uppercase tracking-widest text-zinc-400">Unit System</span>
                <div className="flex items-center bg-zinc-950 border border-zinc-800 rounded px-1 py-0.5">
                  {['metric', 'imperial'].map(sys => (
                    <button
                      key={sys}
                      onClick={() => setUnitSystem(sys)}
                      className={`px-3 py-1 text-[11px] font-mono uppercase tracking-wider rounded transition-colors ${
                        unitSystem === sys ? 'bg-zinc-800 text-zinc-100' : 'text-zinc-500 hover:text-zinc-400'
                      }`}
                    >
                      {sys}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="mb-8 flex-1">
              <div className="flex items-center gap-2 mb-4">
                <Cpu className="text-zinc-500" size={14}/>
                <h4 className="text-xs font-mono uppercase tracking-widest text-zinc-500 m-0">Neural Engine</h4>
              </div>
              <h5 className="text-[10px] font-mono uppercase tracking-widest text-zinc-600 mb-2">Calculation Log</h5>
              <div className="bg-zinc-900/50 p-4 rounded border border-zinc-800 font-mono text-xs leading-relaxed text-zinc-500 max-h-[240px] overflow-y-auto custom-scrollbar">
                {status?.breakdown ? (
                  <div>
                    <div className="text-[#0ea5e9] mb-2">// Health Algorithm (MLP)</div>
                    <div>Base Score: <span className="text-zinc-300">{status.breakdown.base_mlp_score?.toFixed(1) || '0.0'}</span></div>

                    <div>PM2.5 Penalty: <span className="text-[#f43f5e]">{status.breakdown.pm25_penalty?.toFixed(1) || '0.0'}</span></div>
                    <div className="border-t border-zinc-800 mt-2 pt-2">
                      Final IAQ: <span className="text-zinc-100 text-sm">{status.breakdown.final_score || '0'}</span>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-4 text-zinc-600">Awaiting payload...</div>
                )}
              </div>
            </div>
            
            <div className="mt-auto pt-4 border-t border-zinc-800 flex justify-between text-[10px] font-mono uppercase tracking-widest text-zinc-600">
              <span>Core v2.0.0</span>
              <span>AirVita OS</span>
            </div>
          </aside>
        </>
      )}

      {/* ──────────── ALERTS / MODALS ──────────── */}
      {error && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 w-full max-w-md px-4">
          <div className="bg-[#e11d48] text-white p-3 rounded flex items-center gap-3 shadow-[0_0_20px_rgba(225,29,72,0.4)] border border-[#f43f5e]">
            <AlertCircle size={16} />
            <p className="text-xs font-mono uppercase tracking-wider m-0">{error}</p>
          </div>
        </div>
      )}

      {isScannerOpen && <RoomScanner deviceId={activeMonitorId} onClose={() => setIsScannerOpen(false)} />}
      {isPairingOpen && <MobilePairing deviceId={activeMonitorId} onClose={() => setIsPairingOpen(false)} />}
    </div>
  )
}
