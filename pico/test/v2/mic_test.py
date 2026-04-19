import machine
import struct
import time
import math

# --- CONFIGURATION ---
SCK_PIN = 16
WS_PIN = 17
SD_PIN = 18

SAMPLE_RATE = 16000
BITS_PER_SAMPLE = 32
BUFFER_SIZE = 32768

# Calibration/Filtering
# Observations show hardware glitches hit exactly ~8.38M (0x7FFFFF)
GLITCH_THRESHOLD = 8000000 
ALPHA = 0.05 # Baseline smoothing factor

# UI
BAR_WIDTH = 50
MAX_RMS = 50000 # Scaling for talking volume

# --- INITIALIZATION ---
print("\n" + "="*45)
print("--- STABILIZED MIC METER (INMP441) ---")
print("Status: Hardware Glitch Filtering Active")
print("="*45)

# Configure I2S
mic = machine.I2S(0, 
                  sck=machine.Pin(SCK_PIN), 
                  ws=machine.Pin(WS_PIN), 
                  sd=machine.Pin(SD_PIN),
                  mode=machine.I2S.RX, 
                  bits=BITS_PER_SAMPLE, 
                  format=machine.I2S.STEREO,
                  rate=SAMPLE_RATE, 
                  ibuf=BUFFER_SIZE)

SAMPLES_PER_READ = 256
read_buf = bytearray(SAMPLES_PER_READ * 8)

def get_clean_samples():
    """Reads samples and filters out 8.38M hardware spikes."""
    bytes_read = mic.readinto(read_buf)
    if bytes_read == 0:
        return []
    
    count = bytes_read // 4
    raw = struct.unpack(f'<{count}i', read_buf[:bytes_read])
    
    clean = []
    # Only look at Left channel [0, 2, 4...]
    for i in range(0, count, 2):
        s = raw[i] >> 8
        # REJECT spikes that hit the ceiling or floor of the 24-bit range
        if abs(s) < GLITCH_THRESHOLD:
            clean.append(s)
            
    return clean

def run_loop():
    baseline = 0
    active_samples = 0
    
    print("\nStabilizing Mic (0.5s)...")
    start_stab = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start_stab) < 500:
        mic.readinto(read_buf) # Drain startup noise
        
    print("Starting Meter. Press Ctrl+C to stop.\n")
    
    try:
        while True:
            samples = get_clean_samples()
            if not samples:
                # If everything was a glitch, we just skip this frame
                continue
            
            # 1. Update Baseline (DC Offset removal)
            current_avg = sum(samples) / len(samples)
            if baseline == 0:
                baseline = current_avg
            else:
                baseline = (ALPHA * current_avg) + ((1 - ALPHA) * baseline)
            
            # 2. Calculate RMS from valid samples
            sum_sq = sum((s - baseline)**2 for s in samples)
            rms = math.sqrt(sum_sq / len(samples))
            
            # 3. Peak detection
            peak = max(abs(s - baseline) for s in samples)
            
            # 4. Visualization
            # Scale RMS to bar
            bar_len = int(min(BAR_WIDTH, (rms / MAX_RMS) * BAR_WIDTH))
            bar = "#" * bar_len + "-" * (BAR_WIDTH - bar_len)
            
            # Print status
            # We show a small [!] if we had many glitches (short clean list)
            glitch_indicator = " [!]" if len(samples) < (SAMPLES_PER_READ * 0.5) else "    "
            print(f"VOL: [{bar}] | RMS: {int(rms):5d} | PEAK: {int(peak):6d}{glitch_indicator}", end="\r")
            
            time.sleep(0.02) # Fast update

    except KeyboardInterrupt:
        print("\n\nStopping...")
    finally:
        mic.deinit()
        print("I2S Deinitialized.")

if __name__ == "__main__":
    run_loop()
