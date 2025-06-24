from sqlalchemy import create_engine
from models import Base
from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables from .env in the parent directory
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

# Create tables
Base.metadata.create_all(engine)