import httpx
import asyncio
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class WeatherService:
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.aqi_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
        self.geo_url = "https://ipapi.co/json/"
        self.last_weather = None
        self.location = None

    async def get_location(self) -> Optional[Dict]:
        """Fetch location based on IP."""
        if self.location:
            return self.location
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(self.geo_url, timeout=5.0)
                if resp.status_code == 200:
                    data = resp.json()
                    self.location = {
                        "lat": data.get("latitude"),
                        "lon": data.get("longitude"),
                        "city": data.get("city"),
                        "region": data.get("region"),
                        "country": data.get("country_name")
                    }
                    logger.info(f"📍 Geolocation: {self.location['city']}, {self.location['country']}")
                    return self.location
        except Exception as e:
            logger.error(f"Geolocation failed: {e}")
        
        # Fallback to New York
        return {"lat": 40.7128, "lon": -74.0060, "city": "New York", "country": "USA"}

    async def fetch_weather(self) -> Optional[Dict]:
        """Fetch weather and AQI for current location."""
        loc = await self.get_location()
        if not loc:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                # Fetch Weather
                w_params = {
                    "latitude": loc["lat"],
                    "longitude": loc["lon"],
                    "current": "temperature_2m,relative_humidity_2m,surface_pressure"
                }
                # Fetch AQI
                a_params = {
                    "latitude": loc["lat"],
                    "longitude": loc["lon"],
                    "current": "pm2_5,us_aqi"
                }

                w_task = client.get(self.base_url, params=w_params)
                a_task = client.get(self.aqi_url, params=a_params)
                
                w_resp, a_resp = await asyncio.gather(w_task, a_task)

                weather_data = {}
                if w_resp.status_code == 200:
                    curr = w_resp.json().get("current", {})
                    weather_data.update({
                        "temperature_c": curr.get("temperature_2m"),
                        "humidity_pct": curr.get("relative_humidity_2m"),
                        "pressure_hpa": curr.get("surface_pressure"),
                    })
                
                if a_resp.status_code == 200:
                    curr = a_resp.json().get("current", {})
                    weather_data.update({
                        "pm25_ugm3": curr.get("pm2_5"),
                        "aqi": curr.get("us_aqi"),
                        "voc_ppb": 0 # Open-Meteo doesn't provide VOCs easily, default to 0
                    })
                
                weather_data["location"] = f"{loc['city']}, {loc['country']}"
                self.last_weather = weather_data
                return weather_data

        except Exception as e:
            logger.error(f"Weather fetch failed: {e}")
            return self.last_weather # Return cached if available

weather_service = WeatherService()
