import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///gated_manila.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TURNSTILE_SITE_KEY = os.environ.get("TURNSTILE_SITE_KEY", "")
    TURNSTILE_SECRET_KEY = os.environ.get("TURNSTILE_SECRET_KEY", "")

    # Spam protection: max submissions per visitor (by IP address)
    SUBMIT_RATE_LIMIT = os.environ.get("SUBMIT_RATE_LIMIT", "5 per hour")
    RATELIMIT_STORAGE_URI = "memory://"

    # Metro Manila view: center and zoom
    MAP_CENTER = (14.5995, 121.0244)
    MAP_ZOOM = 11
