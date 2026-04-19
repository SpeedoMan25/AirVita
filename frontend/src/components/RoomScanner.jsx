import React, { useRef, useEffect, useState } from 'react';
import './RoomScanner.css';

const API_BASE = '';

export default function RoomScanner({ onClose }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [result, setResult] = useState({ room: 'Initializing...', confidence: 0 });
  const [error, setError] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);

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
          body: JSON.stringify({ image: base64Image })
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
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
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
                <span>{Math.round((result.confidence || 0) * 100)}% Match</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
