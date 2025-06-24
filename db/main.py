from sqlalchemy import create_engine
from models import Base
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

# Create tables
Base.metadata.create_all(engine)