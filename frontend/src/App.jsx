import React, { useState, useEffect, useCallback, useRef } from 'react'
import {
  Activity, Thermometer, Droplets, Sun, Volume2, Gauge, Wind,
  Settings2, X, RefreshCw, AlertCircle, BrainCircuit,
  CheckCircle2, ChevronRight, Camera, Radio, Crosshair, Cpu
} from 'lucide-react'

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
    getStatus: v => v < 18 ? 'COLD' : v < 20 ? 'COOL' : v <= 24 ? 'IDEAL' : v <= 28 ? 'WARM' : 'HOT',
    ranges: [
      { label: 'Cold', max: 18, color: '#3b82f6', text: 'Risk of discomfort, muscles tense up.' },
      { label: 'Cool', max: 20, color: '#0ea5e9', text: 'Slightly below ideal. Fine with layers.' },
      { label: 'Ideal', max: 24, color: '#10b981', text: 'Optimal for health, sleep, and focus.' },
      { label: 'Warm', max: 28, color: '#fb923c', text: 'Comfortable, but productivity may dip.' },
      { label: 'Hot', max: 40, color: '#f43f5e', text: 'Increased fatigue, dehydration risk.' },
    ],
  },
  humidity_pct: {
    label: 'Humidity', shortLabel: 'HUMIDITY', unit: '%', icon: Droplets,
    iconColor: '#0ea5e9', 
    min: 0, max: 100,
    getStatus: v => v < 30 ? 'DRY' : v < 40 ? 'LOW' : v <= 60 ? 'BALANCED' : v <= 70 ? 'HUMID' : 'DAMP',
    ranges: [
      { label: 'Dry', max: 30, color: '#fb923c', text: 'Skin irritation, static electricity.' },
      { label: 'Low', max: 40, color: '#0ea5e9', text: 'Slightly dry; acceptable short-term.' },
      { label: 'Balanced', max: 60, color: '#10b981', text: 'Ideal range for comfort and health.' },
      { label: 'Humid', max: 70, color: '#fbbf24', text: 'Muggy feeling, mold risk increases.' },
      { label: 'Damp', max: 100, color: '#f43f5e', text: 'High mold risk, condensation likely.' },
    ],
  },
  light_lux: {
    label: 'Light', shortLabel: 'LUX', unit: 'lux', icon: Sun,
    iconColor: '#fbbf24', 
    min: 0, max: 1000,
    getStatus: v => v < 100 ? 'DIM' : v < 300 ? 'LOW' : v <= 500 ? 'OPTIMAL' : v <= 800 ? 'BRIGHT' : 'INTENSE',
    ranges: [
      { label: 'Dim', max: 100, color: '#8b5cf6', text: 'Good for sleep and relaxation.' },
      { label: 'Low', max: 300, color: '#0ea5e9', text: 'Casual activities, reading may strain.' },
      { label: 'Optimal', max: 500, color: '#10b981', text: 'Ideal for focused work and study.' },
      { label: 'Bright', max: 800, color: '#fbbf24', text: 'Energizing, but may cause glare.' },
      { label: 'Intense', max: 1000, color: '#f43f5e', text: 'Eye fatigue possible over time.' },
    ],
  },
  noise_db: {
    label: 'Noise', shortLabel: 'NOISE', unit: 'dB', icon: Volume2,
    iconColor: '#8b5cf6', 
    min: 0, max: 100,
    getStatus: v => v < 30 ? 'SILENT' : v < 45 ? 'QUIET' : v <= 55 ? 'MODERATE' : v <= 70 ? 'LOUD' : 'NOISY',
    ranges: [
      { label: 'Silent', max: 30, color: '#10b981', text: 'Perfect for sleep and deep focus.' },
      { label: 'Quiet', max: 45, color: '#0ea5e9', text: 'Library-level. Great for concentration.' },
      { label: 'Moderate', max: 55, color: '#fbbf24', text: 'Normal conversation level.' },
      { label: 'Loud', max: 70, color: '#fb923c', text: 'Sustained exposure causes stress.' },
      { label: 'Noisy', max: 100, color: '#f43f5e', text: 'Hearing protection recommended.' },
    ],
  },
  pressure_hpa: {
    label: 'Pressure', shortLabel: 'PRESSURE', unit: 'hPa', icon: Gauge,
    iconColor: '#10b981', 
    min: 960, max: 1060,
    getStatus: v => v < 1000 ? 'LOW' : v <= 1025 ? 'NORMAL' : 'HIGH',
    ranges: [
      { label: 'Low', max: 1000, color: '#8b5cf6', text: 'Storm system likely. Headaches possible.' },
      { label: 'Normal', max: 1025, color: '#10b981', text: 'Stable conditions. No weather impact.' },
      { label: 'High', max: 1060, color: '#fbbf24', text: 'Clear skies. Dry air may increase.' },
    ],
  },
  pm25_ugm3: {
    label: 'PM 2.5', shortLabel: 'PARTICLES', unit: 'µg/m³', icon: Wind,
    iconColor: '#fb923c', 
    min: 0, max: 150,
    getStatus: v => v < 12 ? 'CLEAN' : v < 35 ? 'MODERATE' : v < 55 ? 'UNHEALTHY' : 'POOR',
    ranges: [
      { label: 'Clean', max: 12, color: '#10b981', text: 'Excellent air. Safe for all groups.' },
      { label: 'Moderate', max: 35, color: '#fbbf24', text: 'Acceptable. Sensitive people may react.' },
      { label: 'Unhealthy', max: 55, color: '#fb923c', text: 'Limit prolonged outdoor exertion.' },
      { label: 'Poor', max: 150, color: '#f43f5e', text: 'Health risk. Use air purification.' },
    ],
  }
}

const ACTIVITY_META = {
  health: {
    label: 'HEALTH BALANCE', id: 'health', color: '#10b981', sub: 'Optimal Airflow',
    ranges: [
      { label: 'Critical', max: 25, color: '#f43f5e', text: 'Severe environmental issues detected.' },
      { label: 'Poor', max: 50, color: '#fb923c', text: 'Multiple factors need improvement.' },
      { label: 'Fair', max: 70, color: '#fbbf24', text: 'Acceptable but room for improvement.' },
      { label: 'Good', max: 85, color: '#10b981', text: 'Healthy environment for all activities.' },
      { label: 'Excellent', max: 100, color: '#059669', text: 'Optimal conditions across all metrics.' },
    ],
    getStatus: v => v < 25 ? 'CRITICAL' : v < 50 ? 'POOR' : v < 70 ? 'FAIR' : v < 85 ? 'GOOD' : 'EXCELLENT',
  },
  sleep: {
    label: 'SLEEP RECOVERY', id: 'sleep', color: '#8b5cf6', sub: 'Poor Conditions',
    ranges: [
      { label: 'Restless', max: 30, color: '#f43f5e', text: 'Too noisy, bright, or warm for sleep.' },
      { label: 'Disturbed', max: 50, color: '#fb923c', text: 'Intermittent disruptions likely.' },
      { label: 'Adequate', max: 70, color: '#fbbf24', text: 'Sleep possible, but not restorative.' },
      { label: 'Restful', max: 85, color: '#8b5cf6', text: 'Good conditions for deep sleep.' },
      { label: 'Optimal', max: 100, color: '#6d28d9', text: 'Dark, cool, quiet — perfect for sleep.' },
    ],
    getStatus: v => v < 30 ? 'RESTLESS' : v < 50 ? 'DISTURBED' : v < 70 ? 'ADEQUATE' : v < 85 ? 'RESTFUL' : 'OPTIMAL',
  },
  work: {
    label: 'WORK FOCUS', id: 'work', color: '#0ea5e9', sub: 'Subdued / Distracted',
    ranges: [
      { label: 'Blocked', max: 30, color: '#f43f5e', text: 'Environment actively disrupts workflow.' },
      { label: 'Struggling', max: 50, color: '#fb923c', text: 'Productivity significantly hampered.' },
      { label: 'Steady', max: 70, color: '#fbbf24', text: 'Manageable but comfort improvements help.' },
      { label: 'Productive', max: 85, color: '#0ea5e9', text: 'Comfortable, well-lit, focused space.' },
      { label: 'Peak', max: 100, color: '#0284c7', text: 'Ideal temperature, light, and air quality.' },
    ],
    getStatus: v => v < 30 ? 'BLOCKED' : v < 50 ? 'STRUGGLING' : v < 70 ? 'STEADY' : v < 85 ? 'PRODUCTIVE' : 'PEAK',
  },
  fun: {
    label: 'SOCIAL ATMOSPHERE', id: 'fun', color: '#f43f5e', sub: 'Vibrant & Electric',
    ranges: [
      { label: 'Dull', max: 30, color: '#71717a', text: 'Environment feels flat and uninviting.' },
      { label: 'Subdued', max: 50, color: '#fbbf24', text: 'Lacks vibrancy for social activities.' },
      { label: 'Pleasant', max: 70, color: '#10b981', text: 'Comfortable for casual socializing.' },
      { label: 'Vibrant', max: 85, color: '#f43f5e', text: 'Lively, warm, and engaging atmosphere.' },
      { label: 'Electric', max: 100, color: '#e11d48', text: 'Peak social energy. Great for hosting.' },
    ],
    getStatus: v => v < 30 ? 'DULL' : v < 50 ? 'SUBDUED' : v < 70 ? 'PLEASANT' : v < 85 ? 'VIBRANT' : 'ELECTRIC',
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

const RadarMatrix = ({ scores, activeAxisId, activeColor }) => {
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

  return (
    <div className="relative w-full aspect-square max-w-[280px] mx-auto flex items-center justify-center">
      <div 
        className="absolute inset-0 blur-[60px] rounded-full opacity-15" 
        style={{ backgroundColor: '#10b981' }}
      ></div>
      
      <svg viewBox="0 0 200 200" className="w-full h-full overflow-visible relative z-10">
        {[25, 50, 75, 100].map((tier, i) => {
          const pts = axes.map(a => `${getCoord(tier, a.angle).x},${getCoord(tier, a.angle).y}`).join(' ');
          return <polygon key={i} points={pts} fill="none" stroke="#27272a" strokeWidth="1" strokeDasharray={i === 3 ? "none" : "2 4"} />;
        })}
        
        {axes.map((a, i) => {
          const pt = getCoord(100, a.angle);
          return (
            <g key={i}>
              <line x1={center} y1={center} x2={pt.x} y2={pt.y} stroke={a.color} strokeWidth="1" strokeOpacity="0.5" />
              <text 
                x={center + (radius + 24) * Math.cos(a.angle * Math.PI / 180)} 
                y={center + (radius + 24) * Math.sin(a.angle * Math.PI / 180)} 
                fill={a.color} 
                fontSize="11" fontFamily="monospace"
                textAnchor="middle" dominantBaseline="middle"
                className="font-bold"
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
              className="transition-all duration-700 ease-out"
            />
          );
        })}
      </svg>
    </div>
  );
};

const AreaChart = ({ history, sensorKey, color, unitSystem }) => {
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
  const lastPoint = getXY(data[data.length - 1], data.length - 1);

  return (
    <div className="w-full h-full relative">
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
        <circle cx={lastPoint[0]} cy={lastPoint[1]} r="2" fill={color} style={{ transition: 'all 500ms linear' }} className="animate-pulse" />
      </svg>
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

  /* ── Data Fetching ── */
  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/current-status?device_id=${activeMonitorId}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setStatus(data)
      if (data.reading) {
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

  const reading = status?.reading ?? null
  const connected = status?.connected ?? false

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
          
          <div className="hidden sm:flex items-center gap-4 font-mono text-xs text-zinc-500 uppercase tracking-widest">
            <span className="flex items-center gap-1.5">
              <Radio size={12} className={connected ? "text-[#10b981] animate-pulse" : "text-zinc-600"}/> 
              SERVER: {connected ? 'CONNECTED' : 'DISCONNECTED'}
            </span>
            <span>STREAM: {connected ? 'ACTIVE' : 'PAUSED'}</span>
          </div>
        </div>

        <div className="flex items-center h-full gap-4">
          <div className="flex items-center bg-zinc-900/50 border border-zinc-800 rounded px-1 py-0.5">
            {['metric', 'imperial'].map(sys => (
              <button
                key={sys}
                onClick={() => setUnitSystem(sys)}
                className={`px-3 py-1 text-[11px] font-mono uppercase tracking-wider rounded transition-colors ${
                  unitSystem === sys ? 'bg-zinc-800 text-zinc-100' : 'text-zinc-500 hover:text-zinc-400'
                }`}
              >
                {sys.substring(0,3)}
              </button>
            ))}
          </div>

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
            <button
              onClick={() => (/iPhone|iPad|iPod|Android/i.test(navigator.userAgent) ? setIsScannerOpen(true) : setIsPairingOpen(true))}
              className="text-xs font-mono text-zinc-400 hover:text-zinc-100 transition-colors uppercase tracking-widest flex items-center gap-1.5"
            >
              <Crosshair size={14} /> <span className="hidden sm:inline">Init Scan</span>
            </button>
            <button onClick={() => setIsTechOpen(!isTechOpen)} className="text-zinc-500 hover:text-zinc-300">
              <Settings2 size={16} />
            </button>
          </div>
        </div>
      </header>

      {/* ──────────── MAIN: Two Horizontal Bands ──────────── */}
      <main className="flex-1 min-h-0 flex flex-col">

        {/* ═══ TOP BAND: Radar + Focus Details + AI Insights ═══ */}
        <div className="h-[50%] flex min-h-0 border-b border-zinc-800/80">

          {/* ── Radar Matrix ── */}
          <div className="w-[28%] min-w-[220px] relative flex items-center justify-center border-r border-zinc-800/80 bg-zinc-950/30 p-4">
            <div className="absolute top-3 left-4 flex items-center gap-2">
              <Cpu size={14} className="text-zinc-500" />
              <span className="text-xs font-mono text-zinc-500 uppercase tracking-widest">Composite Matrix</span>
            </div>
            <RadarMatrix scores={scoreData} activeAxisId={isActivity ? lookupKey : null} activeColor={activeColor} />
          </div>

          {/* ── Current Focus — Threshold Details ── */}
          <div className="w-[320px] xl:w-[360px] shrink-0 flex flex-col min-w-0 border-r border-zinc-800/80 bg-[#09090b]">
            
            {/* Focus Header */}
            <div className="px-5 py-4 flex items-center justify-between bg-zinc-900/20 border-b border-zinc-800/50 shrink-0">
              <span className="text-base font-mono text-zinc-400 uppercase tracking-widest">
                Focus: <span className="font-semibold transition-colors duration-500" style={{ color: activeColor }}>{activeMeta?.label || activeMeta?.shortLabel || 'SYSTEM'}</span>
              </span>
              <span className="text-base font-mono font-semibold transition-colors duration-500" style={{ color: activeColor }}>
                [{displayActiveValue} {isActivity ? 'PTS' : (CONVERSIONS[rawKey]?.[unitSystem]?.unit || activeMeta?.unit)}]
              </span>
            </div>

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

          {/* ── AI Insights / Scanner ── */}
          <div className="flex-1 flex flex-col bg-[#09090b] min-h-0 min-w-[300px]">

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
            <div className="h-28 shrink-0 border-b border-zinc-800/80 bg-zinc-950 relative overflow-hidden flex items-center justify-center group">
              <div className="absolute inset-0" style={{ backgroundImage: 'linear-gradient(#18181b 1px, transparent 1px), linear-gradient(90deg, #18181b 1px, transparent 1px)', backgroundSize: '12px 12px' }}></div>
              
              {(analysisLoading || (status?.pairing_status === 'connected')) && (
                <div className="absolute top-0 left-0 right-0 h-0.5 opacity-50 animate-[scan_3s_ease-in-out_infinite] transition-colors duration-500" style={{ backgroundColor: activeColor, boxShadow: `0 0 8px ${activeColor}` }}></div>
              )}
              
              <div className="relative z-10 text-center px-4 w-full">
                {analysisError ? (
                  <>
                    <AlertCircle size={20} className="mx-auto text-[#f43f5e] mb-1" />
                    <span className="text-xs font-mono text-[#f43f5e] uppercase tracking-widest block">{analysisError}</span>
                  </>
                ) : status?.pairing_status === 'ready' ? (
                  <>
                    <Camera size={24} className="mx-auto text-zinc-600 mb-2 transition-colors duration-500 group-hover:text-zinc-400" />
                    <span className="text-xs font-mono text-zinc-500 uppercase tracking-widest block">Awaiting Mobile Link</span>
                    <button onClick={() => setIsPairingOpen(true)} className="text-[10px] font-mono text-zinc-400 underline mt-2 hover:text-zinc-200">Initialize Scanner</button>
                  </>
                ) : status?.pairing_status === 'connected' ? (
                  <>
                    <Radio size={24} className="mx-auto text-blue-500 mb-2 animate-pulse" />
                    <span className="text-xs font-mono text-blue-400 uppercase tracking-widest block font-bold">Device Link Established</span>
                    <span className="text-[10px] font-mono text-zinc-500 block mt-1 uppercase">Continue scanning on your phone...</span>
                  </>
                ) : (
                  <div className="flex flex-col items-center">
                    <div className="flex items-center gap-3 mb-2">
                       <CheckCircle2 size={20} className="text-emerald-500" />
                       <span className="text-sm font-mono uppercase tracking-[0.2em] text-emerald-500 font-bold">{status?.room_context?.room_type || 'ROOM'} SYNC'D</span>
                    </div>
                    {status?.room_context?.identified_objects?.length > 0 && (
                      <div className="flex flex-wrap justify-center gap-1.5 max-w-[280px]">
                        {status.room_context.identified_objects.slice(0, 5).map((obj, i) => (
                          <span key={i} className="text-[10px] font-mono bg-zinc-800 text-zinc-400 px-1.5 py-0.5 rounded uppercase">{obj}</span>
                        ))}
                      </div>
                    )}
                    <button onClick={resetPairing} className="text-[10px] font-mono text-zinc-500 hover:text-zinc-300 uppercase mt-3 border border-zinc-800 px-3 py-1 rounded">New Scan</button>
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
        </div>

        {/* ═══ BOTTOM BAND: Full-Width Telemetry Grid ═══ */}
        <div className="flex-1 flex flex-col min-h-0 bg-zinc-950">
          <div className="px-5 py-4 border-b border-zinc-800/80 flex justify-between items-center bg-[#09090b] shrink-0">
            <span className="text-sm font-mono text-zinc-500 uppercase tracking-widest flex items-center gap-2">
              <Activity size={16} /> Live Telemetry Feed
            </span>
            {lastFetch && (
              <span className="text-xs font-mono text-zinc-600 uppercase">SYNC: {lastFetch.toLocaleTimeString()}</span>
            )}
          </div>
          
          <div className="flex-1 grid grid-cols-12 gap-x-[3px] gap-y-[6px] p-[3px] bg-zinc-800/40 overflow-hidden">
              {Object.keys(SENSOR_META).map((key, idx) => {
                const meta = SENSOR_META[key];
                const isActive = activeSensorKey === key;
                const rawVal = reading?.[key];
                const numericVal = rawVal != null ? (CONVERSIONS[key]?.[unitSystem]?.convert(rawVal) ?? rawVal) : null;
                
                return (
                  <div 
                    key={key} 
                    onClick={() => setActiveSensorKey(key)}
                    className={`col-span-4 bg-[#09090b] relative p-4 flex flex-col group overflow-hidden cursor-pointer transition-colors ${isActive ? 'bg-zinc-900/40' : ''}`}
                  >
                    <div className="absolute inset-0 opacity-0 group-hover:opacity-10 transition-opacity duration-500 pointer-events-none" style={{ background: `radial-gradient(circle at top right, ${meta.iconColor}, transparent 70%)` }}></div>
                    {isActive && <div className="absolute top-0 left-0 right-0 h-[1px]" style={{ backgroundColor: meta.iconColor, boxShadow: `0 0 8px ${meta.iconColor}`}}></div>}
                    
                    <div className="flex justify-between items-start z-10 shrink-0">
                      <div className="flex items-center gap-2">
                        <meta.icon size={16} style={{ color: isActive ? meta.iconColor : '#71717a' }} />
                        <span className={`text-xs xl:text-sm font-mono tracking-widest ${isActive ? 'text-zinc-200' : 'text-zinc-400'}`}>{meta.shortLabel}</span>
                      </div>
                      <span className={`text-[11px] xl:text-xs font-mono px-2 py-0.5 rounded-sm border ${isActive ? 'border-zinc-600 text-zinc-300' : 'border-zinc-800 text-zinc-600'}`}>{rawVal != null ? meta.getStatus(rawVal) : 'OFF'}</span>
                    </div>
                    <div className="flex items-baseline gap-1 mt-3 z-10 shrink-0">
                      <span className={`text-4xl xl:text-5xl font-light tracking-tighter ${isActive ? 'text-white' : 'text-zinc-300'}`}>
                        {numericVal != null ? <AnimatedNumber value={numericVal} decimals={1} /> : '--'}
                      </span>
                      <span className="text-sm xl:text-base font-mono text-zinc-500">{CONVERSIONS[key]?.[unitSystem]?.unit || meta.unit}</span>
                    </div>
                     {key === 'pm25_ugm3' && (
                      <div className="flex gap-2 text-[9px] xl:text-[10px] font-mono text-zinc-500 uppercase mt-2 z-10 w-full tracking-tighter">
                         <span className="text-zinc-400 font-bold">[PART.]</span>
                         <span>&gt;0.3u: {reading?.pc_0_3 ?? '--'}</span>
                         <span className="text-zinc-700">|</span>
                         <span>&gt;0.5u: {reading?.pc_0_5 ?? '--'}</span>
                         <span className="text-zinc-700">|</span>
                         <span>&gt;1.0u: {reading?.pc_1_0 ?? '--'}</span>
                      </div>
                    )}
                    <div className="flex-1 min-h-0 pt-1 z-10 pr-2">
                      <AreaChart history={history} sensorKey={key} color={meta.iconColor} unitSystem={unitSystem} />
                    </div>
                  </div>
                )
              })}
          </div>
        </div>

      </main>

      {/* ──────────── SETTINGS DRAWER ──────────── */}
      {isTechOpen && (
        <>
          <div onClick={() => setIsTechOpen(false)} className="fixed inset-0 z-40 bg-[#09090b]/60 backdrop-blur-sm" />
          <aside className="fixed top-0 left-0 bottom-0 z-50 w-full max-w-[380px] bg-[#09090b] border-r border-zinc-800 shadow-2xl p-6 flex flex-col overflow-y-auto custom-scrollbar animate-[slideIn_0.2s_ease-out]">
            <div className="flex items-center justify-between mb-8 border-b border-zinc-800 pb-4">
              <div className="flex items-center gap-3">
                <Cpu className="text-zinc-500" size={18}/>
                <h3 className="text-sm font-mono uppercase tracking-widest text-zinc-100 m-0">Neural Engine</h3>
              </div>
              <button onClick={() => setIsTechOpen(false)} className="text-zinc-500 hover:text-zinc-300 transition-colors">
                <X size={20} />
              </button>
            </div>

            <div className="mb-8">
              <h4 className="text-xs font-mono uppercase tracking-widest text-zinc-500 mb-4">Neural Override {scenarios.length > 0 ? `(${scenarios.length})` : '(Loading...)'}</h4>
              <div className="flex flex-col gap-2">
                <button
                  onClick={() => selectScenario('live')}
                  className={`flex items-center justify-between p-3 rounded border font-mono text-xs uppercase tracking-widest transition-colors ${!manualScenarioId || manualScenarioId === 'live' ? 'border-[#10b981] bg-[#10b981]/10 text-[#10b981]' : 'border-zinc-800 bg-zinc-900/50 text-zinc-400 hover:bg-zinc-800'}`}
                >
                  <span className="flex items-center gap-2"><Radio size={16} /> Live Hardware Feed</span>
                  <ChevronRight size={16} />
                </button>
                {scenarios.map(s => (
                  <button
                    key={s.id} onClick={() => selectScenario(s.id)}
                    className={`flex items-center justify-between p-3 rounded border font-mono text-xs uppercase tracking-widest transition-colors ${manualScenarioId === s.id ? 'border-[#0ea5e9] bg-[#0ea5e9]/10 text-[#0ea5e9]' : 'border-zinc-800 bg-zinc-900/50 text-zinc-400 hover:bg-zinc-800'}`}
                  >
                    <span className="flex items-center gap-2"><span className="text-base">{s.icon}</span> {s.name}</span>
                    <ChevronRight size={16} />
                  </button>
                ))}
              </div>
            </div>

            <div className="mb-8 flex-1">
              <h4 className="text-xs font-mono uppercase tracking-widest text-zinc-500 mb-4">Calculation Log</h4>
              <div className="bg-zinc-950 p-4 rounded border border-zinc-800 font-mono text-xs leading-relaxed text-zinc-500 max-h-[240px] overflow-y-auto custom-scrollbar">
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
