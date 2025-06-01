from litellm import completion
from dotenv import load_dotenv
load_dotenv()
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def openai():
    response = completion(
        model="openai/gpt-4o",
        messages=[{"content": "Hello, how are you?", "role": "user"}]
    )
    print(response)

def gemini():
    response = completion(
        model="gemini/gemini-1.5-flash",
        messages=[{"content": "Hello, how are you?", "role": "user"}]
    )
    print(response)

def gemini2():
    response = completion(
        model="gemini/gemini-2.0-flash-exp",
        messages=[{"content": "Hello, how are you?", "role": "user"}]
    )
    print(response)

# Allow script execution via uv run
if __name__ == "__main__":
    import sys
    fn = sys.argv[1] if len(sys.argv) > 1 else "openai"
    if fn == "openai":
        openai()
    elif fn == "gemini":
        gemini()
    elif fn == "gemini2":
        gemini2()
