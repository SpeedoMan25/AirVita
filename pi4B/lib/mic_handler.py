import numpy as np

class MicrophoneHandler:
    """
    Handler for capturing audio data from an I2S Microphone on Pi 4B.
    Assumes the microphone is configured as the default ALSA input device.
    """
    def __init__(self, sample_rate=44100, chunk_size=1024):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.stream = None
        self.device_index = None
        
        try:
            import sounddevice as sd
            self.sd = sd
            # Attempt to find an I2S or Generic device
            devices = sd.query_devices()
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
                    name = dev['name'].lower()
                    if 'i2s' in name or 'generic' in name or 'snd_rpi' in name:
                        self.device_index = i
                        print(f"🎤 Mic: Found candidate I2S device at index {i}: {dev['name']}")
                        break
            
            if self.device_index is None:
                print("⚠️ Mic: No explicit I2S device found in query_devices. Using system default.")
        except Exception as e:
            self.sd = None
            print(f"Warning: Microphone initialization failed: {e}")

    def get_noise_level(self):
        """
        Captures a chunk of audio and returns the Decibel (dB) level.
        """
        if not self.sd:
            return 0.0

        try:
            # Capture a small chunk of audio
            duration = 0.2 # Slightly longer for stability
            audio_data = self.sd.rec(int(duration * self.sample_rate), 
                                    samplerate=self.sample_rate, 
                                    channels=1, 
                                    device=self.device_index,
                                    blocking=True)
            
            # Calculate RMS
            rms = np.sqrt(np.mean(audio_data**2))
            
            # Convert to dB (relative to an arbitrary reference)
            if rms > 1e-6: # Avoid log of zero
                db = 20 * np.log10(rms) + 94
            else:
                db = 30.0 # Floor
                
            return round(db, 2)
        except Exception as e:
            print(f"⚠️ Mic Capture Error (Check I2S overlay): {e}")
            return 0.0
