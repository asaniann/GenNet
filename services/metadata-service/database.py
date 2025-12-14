"""Database config"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os
from models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://gennet:gennet_dev@postgres:5432/gennet")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)

