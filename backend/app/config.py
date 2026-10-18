import os

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/incidents"
)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

CHANNEL = "incident-monitor:stream"
STATS_KEY = "incident-monitor:stats"
STATS_TTL = 10  # seconds

# open an incident automatically when a source logs this many errors in the window
ERROR_THRESHOLD = int(os.getenv("ERROR_THRESHOLD", "5"))
ERROR_WINDOW = int(os.getenv("ERROR_WINDOW", "60"))
