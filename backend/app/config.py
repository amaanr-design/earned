import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

API_KEY = os.environ.get("API_KEY", "")
DATABASE_PATH = Path(__file__).resolve().parent.parent / "earned.db"

# decisions.md §6 — week one has one user; hardcode which one.
EARNED_USER_ID = os.environ.get("EARNED_USER_ID", "u_default")
