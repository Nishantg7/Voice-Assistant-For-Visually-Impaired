import requests
import json
from datetime import datetime

class WeatherService:
    def __init__(self):
        # Using OpenWeatherMap API (free tier)
        self.api_key = "your_api_key_here"  # User will need to add their own API key
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"

    def get_weather(self, city_name):
        """Get current weather information for a city"""
        try:
            # Make API request
            params = {
                'q': city_name,
                'appid': self.api_key,
                'units': 'metric'  # Use Celsius
            }

            response = requests.get(self.base_url, params=params)
            response.raise_for_status()

            data = response.json()

            # Extract relevant information
            weather_desc = data['weather'][0]['description']
            temp = data['main']['temp']
            humidity = data['main']['humidity']
            wind_speed = data['wind']['speed']

            # Format the weather information
            weather_info = f"The weather in {city_name} is {weather_desc}. "
            weather_info += f"Temperature is {temp} degrees Celsius. "
            weather_info += f"Humidity is {humidity} percent. "
            weather_info += f"Wind speed is {wind_speed} meters per second."

            return weather_info

        except requests.exceptions.RequestException as e:
            return f"Sorry, I couldn't fetch weather information for {city_name}. Error: {str(e)}"
        except KeyError as e:
            return f"Sorry, I couldn't parse weather data for {city_name}. Please check the city name."

def get_weather_info(city_name):
    """Simple function to get weather information for testing"""
    weather_service = WeatherService()
    return weather_service.get_weather(city_name)

if __name__ == "__main__":
    # Test the weather function
    print(get_weather_info("London"))
