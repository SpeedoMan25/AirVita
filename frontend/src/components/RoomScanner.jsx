import React, { useRef, useEffect, useState } from 'react';
import { CheckCircle2 } from 'lucide-react';
import './RoomScanner.css';

const API_BASE = import.meta.env.DEV ? '' : (import.meta.env.VITE_API_URL || '');

export default function RoomScanner({ onClose, deviceId }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [result, setResult] = useState({ room: 'Initializing...', confidence: 0 });
  const [error, setError] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isLocked, setIsLocked] = useState(false);
  const [isPairingComplete, setIsPairingComplete] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    let stream = null;

    async function startCamera() {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'environment', width: { ideal: 640 }, height: { ideal: 640 } },
          audio: false
        });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          setIsStreaming(true);

          // Inform backend that mobile is linked
          fetch(`${API_BASE}/api/pairing/status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_id: deviceId, status: 'connected' })
          }).catch(console.error);
        }
      } catch (err) {
        console.error("Camera access error:", err);
        setError("Camera access denied. Please allow permissions and use HTTPS.");
      }
    }

    startCamera();

    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  useEffect(() => {
    if (!isStreaming) return;

    const interval = setInterval(async () => {
      if (!videoRef.current || !canvasRef.current) return;

      const canvas = canvasRef.current;
      const video = videoRef.current;
      const ctx = canvas.getContext('2d');

      // Draw frame to hidden canvas
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const base64Image = canvas.toDataURL('image/jpeg', 0.5);

      try {
        const res = await fetch(`${API_BASE}/api/scan-room`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ image: base64Image, device_id: deviceId })
        });

        if (res.ok) {
          const data = await res.json();
          setResult(data);
        }
      } catch (err) {
        console.error("Frame upload failed:", err);
      }
    }, 500); // 2 FPS is plenty and saves bandwidth

    return () => clearInterval(interval);
  }, [isStreaming]);

  return (
    <div className="room-scanner">
      {error ? (
        <div className="room-scanner__error">
          <p>{error}</p>
          <button className="room-scanner__close" onClick={onClose}>Close</button>
        </div>
      ) : isPairingComplete ? (
        <div className="flex flex-col items-center justify-center p-12 text-center h-full bg-[#09090b] text-white">
          <div className="w-20 h-20 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mb-8">
            <CheckCircle2 size={40} className="text-emerald-500" />
          </div>
          <h2 className="text-2xl font-bold mb-4 tracking-tight">Sync Complete</h2>
          <div className="space-y-4 max-w-xs">
            <p className="text-zinc-400 leading-relaxed text-sm">
              Your room context has been exported to the primary dashboard.
            </p>
            <div className="p-4 bg-zinc-900/50 rounded-2xl border border-zinc-800/50">
              <span className="text-zinc-500 text-[10px] uppercase tracking-widest block mb-1">Status</span>
              <span className="text-emerald-500 font-mono text-xs font-bold uppercase">Scanner Dormant</span>
            </div>
            <p className="text-zinc-500 text-xs pt-4">
              Return to your laptop to continue with <br/><strong>Neural AI Analysis</strong>.
            </p>
          </div>
        </div>
      ) : (
        <div className="room-scanner__box">
          <div className="room-scanner__video-wrap">
            <video ref={videoRef} autoPlay playsInline muted />
            <div className="room-scanner__overlay">
              <div className="room-scanner__scan-line" />
            </div>
            <canvas ref={canvasRef} style={{ display: 'none' }} width="480" height="480" />
          </div>

          <div className="room-scanner__content">
            <div className="room-scanner__header">
              <span className="room-scanner__status-dot" />
              <p>Lens View · Live</p>
              <button className="room-scanner__minimize" onClick={onClose}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6 6 18M6 6l12 12" /></svg>
              </button>
            </div>

            <div className="room-scanner__result">
              <h2 className="room-scanner__room-name">{result.room}</h2>
              <div className="room-scanner__confidence">
                <div className="room-scanner__progress-track">
                  <div
                    className="room-scanner__progress-fill"
                    style={{ width: `${(result.confidence || 0) * 100}%` }}
                  />
                </div>
                <span style={{ color: (isLocked || result.confidence > 0.6) ? '#10b981' : 'inherit', fontWeight: (isLocked || result.confidence > 0.6) ? 700 : 'normal' }}>
                  {isLocked ? '✔ Mapping Confirmed' : (result.confidence > 0.6 ? '✔ Locked & Synced' : `${Math.round((result.confidence || 0) * 100)}% Match`)}
                </span>
              </div>

              {result.confidence > 0.5 && !isLocked && (
                <button
                  className="room-scanner__confirm-btn"
                  onClick={async () => {
                    if (isLoading) return;
                    setIsLoading(true);
                    const canvas = canvasRef.current;
                    const video = videoRef.current;
                    if (!canvas || !video) return;

                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                    const base64Image = canvas.toDataURL('image/jpeg', 0.5);

                    try {
                      await fetch(`${API_BASE}/api/scan-room`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ image: base64Image, device_id: deviceId, force_lock: true })
                      });
                      
                      // Inform backend pairing is done
                      await fetch(`${API_BASE}/api/pairing/status`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ device_id: deviceId, status: 'completed' })
                      });

                      setIsLocked(true);
                      setTimeout(() => setIsPairingComplete(true), 1500);
                    } catch (err) {
                      console.error("Locking failed:", err);
                      setIsLoading(false);
                    }
                  }}
                  disabled={isLoading}
                  style={{
                    marginTop: '16px',
                    width: '100%',
                    padding: '12px',
                    borderRadius: '12px',
                    background: isLoading ? '#3730a3' : '#4f46e5',
                    color: '#fff',
                    border: 'none',
                    fontWeight: 700,
                    fontSize: '14px',
                    cursor: isLoading ? 'not-allowed' : 'pointer',
                    boxShadow: '0 4px 12px rgba(79,70,229,0.2)',
                    opacity: isLoading ? 0.7 : 1
                  }}
                >
                  {isLoading ? 'Uploading results...' : 'Confirm Room Mapping'}
                </button>
              )}

            </div>
          </div>
        </div>
      )}
    </div>
  );
}
