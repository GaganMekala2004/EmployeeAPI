# ==========================
# Topic: Database Configuration
# ==========================

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables from .env
load_dotenv()

# Read Database URL from .env
DATABASE_URL = os.getenv("DATABASE_URL")

# Create Database Engine
engine = create_engine(DATABASE_URL)

# Create Session Factory
SessionLocal = sessionmaker(
    autocommit=False,   # Save changes only after commit()
    autoflush=False,    # Flush changes manually
    bind=engine         # Connect sessions to engine
)

# Base class for all SQLAlchemy Models
Base = declarative_base()