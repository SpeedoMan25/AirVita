import React, { useEffect, useState } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import './MobilePairing.css';

const API_BASE = import.meta.env.DEV ? '' : (import.meta.env.VITE_API_URL || '');

export default function MobilePairing({ onClose }) {
  const [info, setInfo] = useState({ ip: 'Loading...', url: '' });
  const [error, setError] = useState(null);

  useEffect(() => {
    const port = window.location.port ? `:${window.location.port}` : '';
    const host = window.location.hostname;

    // If already on a network IP, use it directly
    if (host !== 'localhost' && host !== '127.0.0.1' && !host.includes('lvh.me') && host !== 'localhost.localdomain') {
      setInfo({ ip: host, url: `https://${host}${port}#scan` });
      return;
    }

    // Try to auto-detect network IP from backend
    fetch(`${API_BASE}/api/connection-info`)
      .then(r => r.json())
      .then(data => {
        if (data.ip && data.ip !== '127.0.0.1') {
          setInfo({ ip: data.ip, url: `https://${data.ip}${port}#scan` });
        } else {
          setInfo({ ip: host, url: `https://${host}${port}#scan` });
          setError("Could not detect network IP. Make sure your PC and phone are on the same Wi-Fi. Try accessing the dashboard using your PC's IP address instead of localhost.");
        }
      })
      .catch(() => {
        setInfo({ ip: host, url: `https://${host}${port}#scan` });
        setError("Could not detect network IP. Make sure your PC and phone are on the same Wi-Fi. Try accessing the dashboard using your PC's IP address instead of localhost.");
      });
  }, []);

  return (
    <div className="pairing-overlay" onClick={onClose}>
      <div className="pairing-card" onClick={e => e.stopPropagation()}>
        <button className="pairing-close" onClick={onClose}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6 6 18M6 6l12 12" /></svg>
        </button>

        <h2>Mobile Scanner Setup</h2>
        <p className="pairing-subtitle">Transform your phone into a live room sensor.</p>

        {error ? (
          <div className="pairing-error" style={{ color: '#d96a5c', padding: '10px 20px', background: 'rgba(217, 106, 92, 0.1)', borderRadius: '12px', lineHeight: '1.6', marginTop: '20px' }}>
            {error}
          </div>
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
