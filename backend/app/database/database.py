import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings, DB_PATH
from pathlib import Path

logger = logging.getLogger("sih26183.db")

# Configure SQLite or PostgreSQL
db_url = settings.DATABASE_URL
connect_args = {}

if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    try:
        raw_path = db_url.replace("sqlite:///", "")
        Path(raw_path).parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

try:
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        echo=False
    )
    # Quick connectivity test
    with engine.connect() as test_conn:
        test_conn.execute(text("SELECT 1"))
    logger.info("Connected to database successfully.")
except Exception as e:
    logger.warning(f"Primary database connection failed: {e}. Falling back to local SQLite at {DB_PATH}")
    sqlite_url = f"sqlite:///{DB_PATH}"
    engine = create_engine(
        sqlite_url,
        connect_args={"check_same_thread": False},
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
