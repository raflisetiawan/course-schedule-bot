import os
from dotenv import load_dotenv

load_dotenv()

# Discord
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash-lite"

# App Config
ACTIVE_SEMESTER = "GN"  # GS = Semester Gasal, GN = Semester Genap
MAX_MESSAGE_LENGTH = 500  # Truncate pesan user sebelum dikirim ke Gemini
RATE_LIMIT_RATE = 10      # Max request per user
RATE_LIMIT_PER = 60.0     # Per berapa detik
