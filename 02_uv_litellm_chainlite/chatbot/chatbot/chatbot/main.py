import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import chainlit as cl
from litellm import completion
import json
from litellm.exceptions import RateLimitError, APIConnectionError

# Load environment variables
load_dotenv()

class RateLimiter:
    """Handles rate limiting for API calls"""
    def __init__(self, max_calls=15, period=60):
        self.max_calls = max_calls
        self.period = timedelta(seconds=period)
        self.calls = []

    def check(self):
        now = datetime.now()
        self.calls = [t for t in self.calls if now - t < self.period]
        if len(self.calls) >= self.max_calls:
            raise Exception("Rate limit exceeded. Please wait a minute before sending more messages.")
        self.calls.append(now)

# Initialize rate limiter
rate_limiter = RateLimiter()

def load_chat_history(session_id):
    """Load chat history from session-specific JSON file"""
    filename = f"chat_history_{session_id}.json"
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_chat_history(session_id, history):
    """Save chat history to session-specific JSON file"""
    filename = f"chat_history_{session_id}.json"
    with open(filename, "w") as f:
        json.dump(history, f, indent=2)

@cl.on_chat_start
async def start():
    """Initialize chat session with custom avatar and loaded history"""
    session_id = cl.user_session.get("id")
    
    # Set custom avatar
    await cl.Avatar(
        name="Strawberry AI",
        url="https://avatars.githubusercontent.com/u/149850206?s=200&v=4"
    ).send()
    
    # Load chat history
    history = load_chat_history(session_id)
    cl.user_session.set("chat_history", history)
    
    welcome_msg = "Welcome to Strawberry AI Assistant! How can I help you today?"
    if history:
        welcome_msg += "\n\nPrevious chat history has been loaded."
    
    await cl.Message(content=welcome_msg).send()

@cl.on_message
async def main(message: cl.Message):
    """Process incoming messages with rate limiting and enhanced error handling"""
    session_id = cl.user_session.get("id")
    history = cl.user_session.get("chat_history", [])
    
    # Process file uploads if any
    if message.elements:
        for element in message.elements:
            if "text/plain" in element.mime:
                message.content += f"\n[Uploaded file content]:\n{element.content.decode()}"
    
    # Add user message to history
    history.append({"role": "user", "content": message.content})
    
    # Create thinking message
    msg = cl.Message(content="Thinking...")
    await msg.send()
    
    try:
        # Check rate limit
        rate_limiter.check()
        
        # Get API key
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("API key not configured")
        
        # Get completion from LiteLLM
        response = completion(
            model="gemini/gemini-2.0-flash",
            api_key=gemini_api_key,
            messages=history,
            temperature=0.7
        )
        
        response_content = response.choices[0].message.content
        
        # Update message with response
        msg.content = response_content
        await msg.update()
        
        # Add assistant response to history
        history.append({"role": "assistant", "content": response_content})
        cl.user_session.set("chat_history", history)
        
        # Log interaction
        print(f"Session {session_id} - User: {message.content[:50]}...")
        print(f"Session {session_id} - Assistant: {response_content[:50]}...")
        
    except RateLimitError:
        msg.content = "⚠️ API rate limit exceeded. Please wait a minute before sending more messages."
        await msg.update()
    except APIConnectionError:
        msg.content = "🔌 Network error. Please check your internet connection."
        await msg.update()
    except Exception as e:
        msg.content = f"❌ Error: {str(e)}"
        await msg.update()
        print(f"Error in session {session_id}: {str(e)}")

@cl.on_chat_end
async def on_chat_end():
    """Save chat history when session ends"""
    session_id = cl.user_session.get("id")
    history = cl.user_session.get("chat_history", [])
    save_chat_history(session_id, history)
    print(f"Session {session_id} - Chat history saved.")