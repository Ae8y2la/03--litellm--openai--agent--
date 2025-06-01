import os
import requests
import json
from dotenv import load_dotenv
import chainlit as cl
from litellm import completion
from typing import Dict, Any

# Load environment variables
load_dotenv()

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
MODEL = "openrouter/meta-llama/llama-3-3-8b-instruct:free"

def get_weather(city: str) -> str:
    """Fetch real weather data from OpenWeatherMap API"""
    try:
        if not WEATHER_API_KEY:
            raise ValueError("OpenWeatherMap API key not configured")
            
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return json.dumps({
            "city": data["name"],
            "country": data["sys"]["country"],
            "temp": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "conditions": data["weather"][0]["description"],
            "wind_speed": data["wind"]["speed"]
        })
    except Exception as e:
        return json.dumps({"error": str(e)})

@cl.on_chat_start
async def start():
    await cl.Avatar(
        name="Weather Poet",
        url="https://cdn-icons-png.flaticon.com/512/1163/1163624.png"
    ).send()
    await cl.Message(
        content="🌸 Welcome to Weather Poet! Tell me a city and I'll compose a haiku about its weather."
    ).send()

@cl.on_message
async def on_message(message: cl.Message):
    msg = cl.Message(content="☁️ Consulting the skies...")
    await msg.send()
    
    try:
        # First get weather data
        weather_data = get_weather(message.content)
        weather_info = json.loads(weather_data)
        
        if "error" in weather_info:
            raise ValueError(weather_info["error"])
        
        # Generate haiku using LLM
        response = completion(
            model=MODEL,
            messages=[{
                "role": "system",
                "content": f"""You are a poetic weather assistant. Create a haiku (5-7-5 syllables) about this weather data:
                {weather_info}
                Then add the raw data at the end."""
            }],
            api_key=OPENROUTER_API_KEY,
            temperature=0.7
        )
        
        msg.content = response.choices[0].message.content
        await msg.update()
        
    except Exception as e:
        msg.content = f"⚡ Error: {str(e)}"
        await msg.update()

if __name__ == "__main__":
    cl.run()