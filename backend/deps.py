# backend/deps.py
from pathlib import Path
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# ------------------------------------------------------------------
#  Load DATABASE_URL from db/.env  (adjust path if your .env lives elsewhere)
# ------------------------------------------------------------------
env_path = Path(__file__).resolve().parents[1] / "db" / ".env"
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in .env")

# ------------------------------------------------------------------
#  SQLAlchemy engine + session
# ------------------------------------------------------------------
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db() -> Session:
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()