from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

from pathlib import Path

# Configure SQLite or PostgreSQL
db_url = settings.DATABASE_URL
connect_args = {}

if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    # Ensure SQLite parent directory exists
    try:
        raw_path = db_url.replace("sqlite:///", "")
        Path(raw_path).parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

engine = create_engine(
    db_url,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
