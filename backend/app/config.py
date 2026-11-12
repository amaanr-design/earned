import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

API_KEY = os.environ.get("API_KEY", "")
DATABASE_PATH = Path(__file__).resolve().parent.parent / "earned.db"

# Browser origins allowed to call the API (CORS). Comma-separated, scheme + host
# (+ port) only — no path, no trailing slash. The default covers `npm run dev`;
# on Render set e.g. CORS_ORIGINS=https://amaanr-design.github.io
CORS_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

# decisions.md §6 — week one has one user; hardcode which one.
EARNED_USER_ID = os.environ.get("EARNED_USER_ID", "u_default")
