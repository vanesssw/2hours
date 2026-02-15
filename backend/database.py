from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# PostgreSQL database (production-ready, supports concurrent connections)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://crackprotocol:crackprotocol_pass@db:5432/crackprotocol"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,        # Connection pool for concurrent users
    max_overflow=20      # Allow up to 30 total connections
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency для получения DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
