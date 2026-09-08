from .auth import router as auth_router
from .cases import router as cases_router
from .wallets import router as wallets_router
from .transactions import router as transactions_router
from .analysis import router as analysis_router
from .evidence import router as evidence_router
from .copilot import router as copilot_router
from .monitoring import router as monitoring_router
from .reports import router as reports_router
from .audit import router as audit_router
from .labels import router as labels_router

__all__ = [
    "auth_router",
    "cases_router",
    "wallets_router",
    "transactions_router",
    "analysis_router",
    "evidence_router",
    "copilot_router",
    "monitoring_router",
    "reports_router",
    "audit_router",
    "labels_router"
]
