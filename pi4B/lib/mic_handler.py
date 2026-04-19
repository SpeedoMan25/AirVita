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
        
        try:
            import sounddevice as sd
            self.sd = sd
        except ImportError:
            self.sd = None
            print("Warning: 'sounddevice' not installed. Noise monitoring will be mocked.")

    def get_noise_level(self):
        """
        Captures a chunk of audio and returns the Decibel (dB) level.
        """
        if not self.sd:
            return 0.0  # No microphone driver available

        try:
            # Capture a small chunk of audio
            duration = 0.1 # seconds
            audio_data = self.sd.rec(int(duration * self.sample_rate), 
                                    samplerate=self.sample_rate, 
                                    channels=1, 
                                    blocking=True)
            
            # Calculate RMS
            rms = np.sqrt(np.mean(audio_data**2))
            
            # Convert to dB (relative to an arbitrary reference)
            # In a real environment, this would be calibrated to a SPL meter
            if rms > 0:
                db = 20 * np.log10(rms) + 94 # Simple shift for demonstration
            else:
                db = 0
                
            return round(db, 2)
        except Exception as e:
            # print(f"Mic Error: {e}")
            return 0.0
