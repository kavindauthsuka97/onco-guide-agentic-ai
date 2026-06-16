# Import os to read database URL from environment variables
import os

# Import Path to create storage folder
from pathlib import Path

# Import create_engine to create database connection engine
from sqlalchemy import create_engine

# Import sessionmaker to create database sessions
from sqlalchemy.orm import sessionmaker

# Import declarative_base to create SQLAlchemy model base class
from sqlalchemy.orm import declarative_base


# Create storage folder if it does not exist
Path("storage").mkdir(parents=True, exist_ok=True)


# Read database URL from environment, or use local SQLite by default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///storage/oncoguide.db",
)


# Create SQLAlchemy database engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
    if DATABASE_URL.startswith("sqlite")
    else {},
)


# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# Create base class for all database models
Base = declarative_base()


# Dependency/helper to get database session
def get_db():

    # Create database session
    db = SessionLocal()

    # Return session safely
    try:

        # Give session to caller
        yield db

    finally:

        # Close session after use
        db.close()