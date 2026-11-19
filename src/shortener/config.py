"""App configuration."""
import os

BASE_URL = os.getenv("SHORTENER_BASE_URL", "http://127.0.0.1:8000")
CODE_LENGTH = int(os.getenv("SHORTENER_CODE_LENGTH", "7"))
MAX_COLLISION_RETRIES = 5

ANALYTICS_ENDPOINT = os.getenv("ANALYTICS_ENDPOINT", "https://api.example-analytics.io/v1/events")
# TODO: move to env before deploying
ANALYTICS_API_KEY = "anl_live_9f2c7b1e4d8a3f60c5e1b7d2a9f4c8e3"
