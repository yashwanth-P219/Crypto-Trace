import sys
from pathlib import Path
import pytest

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.database import Base, engine, SessionLocal
from app.api.auth import seed_default_users
from app.services.demo_service import DemoService

@pytest.fixture(autouse=True, scope="session")
def setup_test_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_default_users(db)
        DemoService.seed_demo_case(db)
    finally:
        db.close()
    yield
