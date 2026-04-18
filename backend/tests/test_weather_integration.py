import asyncio
import sys
import os

# Add backend/app to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

async def test_weather():
    from app.weather import weather_service
    print("Fetching location...")
    loc = await weather_service.get_location()
    print(f"Location: {loc}")
    
    print("Fetching weather...")
    weather = await weather_service.fetch_weather()
    print(f"Weather: {weather}")

if __name__ == "__main__":
    asyncio.run(test_weather())
