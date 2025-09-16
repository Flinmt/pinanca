import os


# Secret used to sign session tokens (HS256)
AUTH_SECRET: str = os.getenv("AUTH_SECRET", "dev-secret-change-me")

# Default token TTL in seconds (1 week by default)
TOKEN_TTL_SECONDS: int = int(os.getenv("AUTH_TOKEN_TTL", str(7 * 24 * 60 * 60)))

# Session file path for local apps (front+back together)
SESSION_FILE: str = os.getenv("SESSION_FILE", os.path.expanduser("~/.pinanca/session.json"))
