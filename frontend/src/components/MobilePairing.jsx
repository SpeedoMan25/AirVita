import React, { useEffect, useState } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import './MobilePairing.css';

const API_BASE = import.meta.env.DEV ? '' : (import.meta.env.VITE_API_URL || '');

export default function MobilePairing({ onClose }) {
  const [info, setInfo] = useState({ ip: 'Loading...', url: '' });
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchIp() {
      try {
        const res = await fetch(`${API_BASE}/api/connection-info`);
        if (!res.ok) throw new Error("Failed to fetch connection info");
        const data = await res.json();
        setInfo(data);
      } catch (err) {
        setError(err.message);
      }
    }
    fetchIp();
  }, []);

  return (
    <div className="pairing-overlay" onClick={onClose}>
      <div className="pairing-card" onClick={e => e.stopPropagation()}>
        <button className="pairing-close" onClick={onClose}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
        </button>
        
        <h2>Mobile Scanner Setup</h2>
        <p className="pairing-subtitle">Transform your phone into a live room sensor.</p>
        
        {error ? (
          <div className="pairing-error">Could not detect LAN IP</div>
        ) : (
          <div className="pairing-qr-section">
            <div className="qr-container">
              {info.url ? (
                <QRCodeSVG 
                  value={info.url} 
                  size={200}
                  bgColor="#ffffff"
                  fgColor="#000000"
                  level="Q"
                  includeMargin={true}
                />
              ) : (
                <div className="qr-placeholder">Loading...</div>
              )}
            </div>
            
            <div className="pairing-instructions">
              <ol>
                <li>Ensure your phone is on the <strong>same Wi-Fi</strong>.</li>
                <li>Scan the code with your phone's camera.</li>
                <li>Accept the browser security warning ("Advanced" &rarr; "Proceed").</li>
                <li>Allow camera permissions.</li>
              </ol>
              <div className="pairing-url-box">
                Or visit: <strong>{info.url}</strong>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
