"""
Database configuration for workflow service
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os
from models import Base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://gennet:gennet_dev@postgres:5432/gennet"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

