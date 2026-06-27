import os
import httpx
from typing import Dict, Any
from dotenv import load_dotenv
load_dotenv()

def get_weather_forecast(location: str) -> Dict[str, Any]:
    """
    Fetches the current weather and a 5-day weather forecast for a given Indian location/city.
    
    Args:
        location: The name of the city, town, or village in India (e.g., "Pune", "Hassan", "Karnal").
        
    Returns:
        A dictionary containing the current temperature, humidity, weather description, 
        and a summary of the 5-day forecast (including expected rainfall and temperatures).
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return {
            "error": "OpenWeatherMap API key is missing. Please set OPENWEATHER_API_KEY in the .env file.",
            "success": False
        }
    
    # Clean location name
    location_query = location.strip()
    loc_clean = location_query.lower()
    indian_states = [
        "karnataka", "maharashtra", "andhra pradesh", "telangana", "tamil nadu", "kerala",
        "gujarat", "rajasthan", "punjab", "haryana", "uttar pradesh", "bihar", "madhya pradesh",
        "west bengal", "odisha", "assam", "himachal pradesh", "uttarakhand", "jammu", "kashmir",
        "jammu & kashmir", "jammu and kashmir", "jharkhand", "chhattisgarh", "goa", "sikkim",
        "manipur", "meghalaya", "mizoram", "nagaland", "tripura", "arunachal pradesh"
    ]
    if loc_clean in indian_states:
        return {
            "error_type": "state_provided",
            "state": location_query,
            "error": f"The location '{location_query}' is an Indian state. You must ask the farmer: 'Which city in {location_query}?'",
            "success": False
        }
        
    if not location_query.lower().endswith("india") and "," not in location_query:
        location_query += ",IN"  # Default to India
        
    try:
        # 1. Fetch current weather
        current_url = f"https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": location_query,
            "appid": api_key,
            "units": "metric"
        }
        
        with httpx.Client(timeout=10.0) as client:
            current_response = client.get(current_url, params=params)
            
            if current_response.status_code != 200:
                # Try without country code as fallback
                params["q"] = location.strip()
                current_response = client.get(current_url, params=params)
                
            if current_response.status_code != 200:
                return {
                    "error": f"Failed to fetch weather for '{location}'. Status code: {current_response.status_code}",
                    "success": False
                }
                
            current_data = current_response.json()
            
            # 2. Fetch 5-day forecast for irrigation planning
            forecast_url = f"https://api.openweathermap.org/data/2.5/forecast"
            forecast_response = client.get(forecast_url, params=params)
            
            forecast_summary = []
            rain_predicted = False
            total_rain = 0.0
            
            if forecast_response.status_code == 200:
                forecast_data = forecast_response.json()
                # Aggregate forecast daily (every 8 intervals is roughly 24 hours)
                # Let's extract key daily indicators
                list_data = forecast_data.get("list", [])
                
                # Check for rain in the next 5 days
                for item in list_data:
                    weather_desc = item.get("weather", [{}])[0].get("main", "").lower()
                    if "rain" in weather_desc:
                        rain_predicted = True
                    rain_info = item.get("rain", {})
                    if rain_info and "3h" in rain_info:
                        total_rain += rain_info["3h"]
                
                # Group by day
                daily_forecasts = {}
                for item in list_data:
                    dt_txt = item.get("dt_txt", "") # "YYYY-MM-DD HH:MM:SS"
                    date = dt_txt.split(" ")[0] if dt_txt else "Unknown"
                    temp = item.get("main", {}).get("temp", 0.0)
                    desc = item.get("weather", [{}])[0].get("description", "clear sky")
                    
                    if date not in daily_forecasts:
                        daily_forecasts[date] = {"temps": [], "descs": []}
                    daily_forecasts[date]["temps"].append(temp)
                    daily_forecasts[date]["descs"].append(desc)
                
                # Format summary
                for date, val in list(daily_forecasts.items())[:5]:
                    avg_temp = sum(val["temps"]) / len(val["temps"])
                    most_common_desc = max(set(val["descs"]), key=val["descs"].count)
                    forecast_summary.append({
                        "date": date,
                        "temp_c": round(avg_temp, 1),
                        "description": most_common_desc
                    })
            
            return {
                "success": True,
                "location": current_data.get("name", location),
                "current": {
                    "temp_c": current_data.get("main", {}).get("temp"),
                    "feels_like_c": current_data.get("main", {}).get("feels_like"),
                    "humidity_pct": current_data.get("main", {}).get("humidity"),
                    "description": current_data.get("weather", [{}])[0].get("description", ""),
                    "wind_speed_mps": current_data.get("wind", {}).get("speed"),
                },
                "forecast": forecast_summary,
                "rain_predicted_next_5_days": rain_predicted,
                "estimated_rainfall_mm": round(total_rain, 1)
            }
            
    except Exception as e:
        return {
            "error": f"An error occurred while fetching weather data: {str(e)}",
            "success": False
        }
