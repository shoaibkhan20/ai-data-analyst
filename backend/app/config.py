import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

config = Config()