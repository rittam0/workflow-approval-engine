"""
Database engine, session factory, and Base.
 
All application code imports `get_db` for dependency injection
and `Base` for model declarations. Nothing else touches the engine directly.
"""
 
import os
 
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
 
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/workflows"
)
 
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
 
 
class Base(DeclarativeBase):
    pass
 
 
def get_db():
    """FastAPI dependency — yields a session, guarantees close."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
 
