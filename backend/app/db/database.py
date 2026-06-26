import os
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Defaults to a local SQLite file — no setup required
DATABASE_URL = os.getenv("DA_DB_URL", "sqlite:///./data/doubleagent.db")

engine = create_engine(
    DATABASE_URL,
    echo=True,
    connect_args={"check_same_thread": False},  # Required for SQLite with FastAPI
)

DBSession = sessionmaker(bind=engine)
