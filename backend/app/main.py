import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.database.database import Base, engine, SessionLocal, get_db
from app.api.auth import seed_default_users
from app.services.demo_service import DemoService

from app.api.auth import router as auth_router
from app.api.cases import router as cases_router
from app.api.wallets import router as wallets_router
from app.api.transactions import router as transactions_router
from app.api.analysis import router as analysis_router
from app.api.evidence import router as evidence_router
from app.api.copilot import router as copilot_router
from app.api.monitoring import router as monitoring_router
from app.api.reports import router as reports_router
from app.api.audit import router as audit_router
from app.api.labels import router as labels_router
from app.api.blockchain_api import router as blockchain_router
from app.api.graph_api import router as graph_router
from app.api.patterns_api import router as patterns_router
from app.api.risk_api import router as risk_router
from app.api.entities_api import router as entities_router
from app.api.investigation_api import router as investigation_router
from app.api.priority_api import router as priority_router
from app.api.chains_api import router as chains_router
from app.api.investigators import router as investigators_router
from app.api.notifications import router as notifications_router
from app.blockchain.chain_registry import ChainRegistry
from app.entities.service import EntityService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("sih26183.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    # Automatically seed default forensic accounts and SIH demo case
    db: Session = SessionLocal()
    try:
        logger.info("Checking and seeding default forensic accounts...")
        seed_default_users(db)
        EntityService.seed_demo_intel(db)
        ChainRegistry.seed_db_networks(db)
        if settings.DEMO_MODE:
            logger.info("Demo Mode active: seeding SIH26183 Hackathon demonstration scenario...")
            DemoService.seed_demo_case(db)
    except Exception as e:
        logger.error(f"Error during startup data initialization: {e}")
    finally:
        db.close()

    yield
    logger.info("Shutting down SIH26183 application...")

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Smart India Hackathon 2026 - Problem Statement SIH26183: "
        "Real-Time Identification of Fraud-Linked Cryptocurrency Exchanges from "
        "Victim-Reported Suspect Wallet Addresses through Automated Blockchain Analytics."
    ),
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers (Both with /api prefix and root aliases for Phase 2 spec compliance)
app.include_router(blockchain_router)
app.include_router(blockchain_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(cases_router)
app.include_router(cases_router, prefix="/api")
app.include_router(wallets_router)
app.include_router(wallets_router, prefix="/api")
app.include_router(transactions_router)
app.include_router(transactions_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")
app.include_router(evidence_router, prefix="/api")
app.include_router(copilot_router, prefix="/api")
app.include_router(monitoring_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(labels_router, prefix="/api")
app.include_router(graph_router)
app.include_router(graph_router, prefix="/api")
app.include_router(patterns_router)
app.include_router(patterns_router, prefix="/api")
app.include_router(risk_router)
app.include_router(risk_router, prefix="/api")
app.include_router(entities_router)
app.include_router(entities_router, prefix="/api")
app.include_router(investigation_router)
app.include_router(investigation_router, prefix="/api")
app.include_router(priority_router)
app.include_router(priority_router, prefix="/api")
app.include_router(chains_router)
app.include_router(chains_router, prefix="/api")
app.include_router(investigators_router)
app.include_router(investigators_router, prefix="/api")
app.include_router(notifications_router)
app.include_router(notifications_router, prefix="/api")

@app.get("/", tags=["System"])
def root_index():
    return {
        "status": "online",
        "app": "CryptoTrace Blockchain Fraud Analytics Platform",
        "message": "CryptoTrace FastAPI backend is running successfully.",
        "documentation": "/docs",
        "health": "/health",
        "api_endpoints": "/api"
    }

@app.get("/health", tags=["System"])
@app.get("/api/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "mode": "DEMO_MODE" if settings.DEMO_MODE else "LIVE_MODE",
        "environment": settings.APP_ENV
    }

@app.get("/database/status", tags=["Database", "System"])
@app.get("/api/database/status", tags=["Database", "System"])
def database_status(db: Session = Depends(get_db)):
    """
    Returns database connection health, engine type (PostgreSQL Supabase vs SQLite), and table row counts.
    """
    from app.database.models import Case, Wallet, Transaction, CaseTransaction
    db_type = "PostgreSQL (Supabase)" if "postgres" in settings.DATABASE_URL.lower() else "SQLite"
    try:
        # Check connection by executing count queries
        case_count = db.query(Case).count()
        wallet_count = db.query(Wallet).count()
        tx_count = db.query(Transaction).count()
        case_tx_count = db.query(CaseTransaction).count()
        return {
            "status": "connected",
            "database": db_type,
            "connected": True,
            "supabase_configured": bool(settings.SUPABASE_URL and settings.SUPABASE_KEY),
            "supabase_project_url": settings.SUPABASE_URL,
            "tables": {
                "cases": case_count,
                "wallets": wallet_count,
                "transactions": tx_count,
                "case_transactions": case_tx_count
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "database": db_type,
            "connected": False,
            "supabase_configured": bool(settings.SUPABASE_URL and settings.SUPABASE_KEY),
            "error": str(e)
        }

@app.get("/api/status", tags=["System"])
def system_status(db: Session = Depends(get_db)):
    from app.database.models import Case, Wallet, Transaction, Alert
    return {
        "active_cases": db.query(Case).count(),
        "indexed_wallets": db.query(Wallet).count(),
        "indexed_transactions": db.query(Transaction).count(),
        "active_alerts": db.query(Alert).filter(Alert.is_read == False).count(),
        "mode": "DEMO_MODE" if settings.DEMO_MODE else "LIVE_MODE",
        "supported_chains": ["Ethereum Sepolia", "Ethereum Mainnet", "Polygon", "BNB Smart Chain"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
