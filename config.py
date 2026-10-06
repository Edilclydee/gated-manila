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
    LOGIN_RATE_LIMIT = os.environ.get("LOGIN_RATE_LIMIT", "10 per 15 minutes")
    RATELIMIT_STORAGE_URI = "memory://"

    # Session cookies. Set SESSION_COOKIE_SECURE=1 in production (HTTPS only).
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"

    # Metro Manila view: center and zoom
    MAP_CENTER = (14.5995, 121.0244)
    MAP_ZOOM = 11
