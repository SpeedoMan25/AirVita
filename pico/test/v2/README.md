# Pico Test V2: Modular Hardware Suite

This is the second iteration of the testing suite, redesigned for a Pico breakout board with shared power rails and a rich sensor array.

## 🔌 Hardware Architecture

| Component | Protocol | Pin Mapping | physical Pin | Power |
| :--- | :--- | :--- | :--- | :--- |
| **I2C LCD** | I2C (0x27) | SDA:GP0, Scl:GP1 | 1, 2 | 5V |
| **NeoPixels (x16)** | One-Wire | DIN: GP2 | 4 | 5V |
| **GY-302 (Light)** | I2C (0x23) | SDA:GP0, Scl:GP1 | 1, 2 | 3.3V |
| **BME688 (Env)** | I2C (0x76/77)| SDA:GP0, Scl:GP1 | 1, 2 | 3.3V |
| **PMS5003 (Air)** | UART1 | TX:GP4, RX:GP5 | 6, 7 | 5V |
| **INMP441 (Mic)** | I2S | SCK:16, WS:17, SD:18 | 21, 22, 24 | 3.3V |
| **Buzzer (Active)** | Digital | Signal: GP15 | 20 | 3.3V |

---

## 🚀 Running the Tests

### Phase 1-3: Core UI
- **LCD Only:** `python -m mpremote connect COM4 run pico/test/v2/lcd_test.py`
- **NeoPixels:** `python -m mpremote connect COM4 run pico/test/v2/neopixel_test.py`
- **Integrated UI:** `python -m mpremote connect COM4 run pico/test/v2/integrated_test.py`

### Phase 4-5: Light & Automation
- **Light Sensor:** `python -m mpremote connect COM4 run pico/test/v2/light_test_v2.py`
- **Master V2:** `python -m mpremote connect COM4 run pico/test/v2/master_v2.py`

### Phase 6: Digital Audio (Active)
- **Microphone:** `python -m mpremote connect COM4 run pico/test/v2/mic_test.py`

### Phase 7-8: Atmosphere & Environmental
- **Air Quality:** `python -m mpremote connect COM4 run pico/test/v2/air_test_v2.py`
- **Environment:** `python -m mpremote connect COM4 run pico/test/v2/bme_test.py` 
  *(Measures Temp, Hum, Pressure, and VOC Gas Resistance)*

### Phase 9: Alerts & Simulations
- **Buzzer:** `python -m mpremote connect COM4 run pico/test/v2/buzzer_test.py`
- **Simulation:** `python -m mpremote connect COM4 run pico/test/v2/bomb_sim.py`
  *(Dramatic 30-second countdown using LCD, LEDs, and Buzzer)*

---

## 🛠 Troubleshooting
- **I2C Bus Not Found?** The BME688 requires `CS` tied to 3.3V and `SDO` tied to GND for stable I2C 0x76 operation.
- **PMS5003 No Data?** Ensure UART RX/TX are crossed correctly (Pico RX ➡ Sensor TX).
- **Audio Zeros?** Check I2S wiring stability on the breadboard; I2S is very sensitive to loose connections.
