from google import genai
from app.config import config

client = genai.Client(api_key=config.GEMINI_API_KEY)
MODEL = "gemini-3.5-flash-lite"

def generate(prompt: str, system: str = "") -> str:
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    response = client.models.generate_content(
        model=MODEL,
        contents=full_prompt,
    )
    return response.text.strip()