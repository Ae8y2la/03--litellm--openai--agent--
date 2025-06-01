import os
import re
import requests
from dotenv import load_dotenv
import chainlit as cl
from litellm import completion
from typing import Dict, Any

# Load environment variables
load_dotenv()

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
# Updated model name with provider prefix
MODEL = "openrouter/meta-llama/llama-3-8b-instruct"

def extract_city(query: str) -> str:
    """Extract city name from natural language query"""
    query = re.sub(r"(what's|what is|weather|forecast|in|for|right now|today|tomorrow)", "", query, flags=re.IGNORECASE)
    city = re.search(r"[a-zA-Z]+(?:\s+[a-zA-Z]+)*", query.strip())
    return city.group(0) if city else ""

def get_weather(city: str) -> Dict[str, Any]:
    """Fetch weather data from OpenWeatherMap"""
    if not city:
        return {"success": False, "error": "No city specified"}
    
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 404:
            return {"success": False, "error": f"City '{city}' not found"}
        
        response.raise_for_status()
        data = response.json()
        
        return {
            "city": data["name"],
            "temp": data["main"]["temp"],
            "conditions": data["weather"][0]["description"].title(),
            "humidity": data["main"]["humidity"],
            "success": True
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@cl.on_chat_start
async def start():
    await cl.Message(
        author="Weather Poet",
        content="🌸 Welcome! Ask me about weather in any city (e.g. 'weather in Paris')"
    ).send()

@cl.on_message
async def on_message(message: cl.Message):
    city = extract_city(message.content)
    if not city:
        await cl.Message(content="Please specify a city name").send()
        return

    checking_msg = await cl.Message(content=f"🌤️ Checking weather for {city}...").send()
    
    weather = get_weather(city)
    
    if not weather["success"]:
        await cl.Message(content=f"⚠️ {weather['error']}").send()
        return
    
    try:
        response = completion(
            model=MODEL,
            messages=[{
                "role": "system",
                "content": f"""Create a short weather poem about:
                City: {weather['city']}
                Temperature: {weather['temp']}°C
                Conditions: {weather['conditions']}
                Humidity: {weather['humidity']}%"""
            }],
            api_base="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY
        )
        
        poem = response.choices[0].message.content
        await cl.Message(content=f"""
        {poem}
        
        📊 Weather Details:
        - City: {weather['city']}
        - Temperature: {weather['temp']}°C
        - Conditions: {weather['conditions']}
        """).send()
        
    except Exception as e:
        await cl.Message(content=f"⚠️ Error: {str(e)}").send()

if __name__ == "__main__":
    cl.run()