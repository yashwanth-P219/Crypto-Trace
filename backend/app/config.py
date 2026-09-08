import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
if (BASE_DIR / "data" / "sih26183.db").exists():
    DATA_DIR = (BASE_DIR / "data").resolve()
elif (BASE_DIR.parent / "data" / "sih26183.db").exists():
    DATA_DIR = (BASE_DIR.parent / "data").resolve()
else:
    DATA_DIR = (BASE_DIR / "data").resolve()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = (DATA_DIR / "sih26183.db").as_posix()

class Settings(BaseSettings):
    APP_NAME: str = "SIH26183 Blockchain Fraud Analytics"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Security
    SECRET_KEY: str = "sih26183_super_secret_forensic_investigation_jwt_key_2026"
    JWT_SECRET: Optional[str] = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres.obcxpsriultifppkskax:mwbYpV4kCJWs5R7V@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"
    )

    # Blockchain RPCs
    ETHEREUM_RPC_URL: str = "https://eth.llamarpc.com"
    SEPOLIA_RPC_URL: str = "https://ethereum-sepolia-rpc.publicnode.com"
    POLYGON_RPC_URL: str = "https://polygon-rpc.com"
    BNB_RPC_URL: str = "https://bsc-dataseed.binance.org"

    # Supabase Configuration
    SUPABASE_URL: Optional[str] = os.getenv(
        "SUPABASE_URL",
        "https://obcxpsriultifppkskax.supabase.co"
    )
    SUPABASE_KEY: Optional[str] = os.getenv(
        "SUPABASE_KEY",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9iY3hwc3JpdWx0aWZwcGtza2F4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg2ODAyMjgsImV4cCI6MjEwNDI1NjIyOH0.bbzfjZybyx4Bt0Y5quu8K7AZY_URdWQIebn2pN8XcGw"
    )

    # Block Explorer & Transaction History API Keys (Optional)
    ETHERSCAN_API_KEY: Optional[str] = None
    POLYGONSCAN_API_KEY: Optional[str] = None
    BSCSCAN_API_KEY: Optional[str] = None
    TRANSACTION_HISTORY_API_URL: str = "https://api-sepolia.etherscan.io/api"
    TRANSACTION_HISTORY_API_KEY: Optional[str] = None
    SEPOLIA_EXPLORER_URL: str = "https://sepolia.etherscan.io"

    # Application Mode
    DEMO_MODE: bool = True

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

# Ensure data directory exists
data_dir = DATA_DIR
data_dir.mkdir(parents=True, exist_ok=True)
address_labels_dir = data_dir / "address_labels"
address_labels_dir.mkdir(parents=True, exist_ok=True)
sample_cases_dir = data_dir / "sample_cases"
sample_cases_dir.mkdir(parents=True, exist_ok=True)
