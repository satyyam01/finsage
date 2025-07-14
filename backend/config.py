import os
from dotenv import load_dotenv

# Load environment variables from .env file (only once, here)
load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://finsage_user:finsage_password@localhost:5432/finsage_db")
DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
DATABASE_NAME = os.getenv("DATABASE_NAME", "finsage_db")
DATABASE_USER = os.getenv("DATABASE_USER", "finsage_user")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "finsage_password")

# Session Configuration
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "your-secret-key-change-this-in-production")
SESSION_EXPIRY_HOURS = int(os.getenv("SESSION_EXPIRY_HOURS", "24")) 