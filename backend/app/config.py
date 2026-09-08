import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = (BASE_DIR.parent / "data").resolve()
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
    DATABASE_URL: str = f"sqlite:///{DB_PATH}"

    # Blockchain RPCs
    ETHEREUM_RPC_URL: str = "https://eth.llamarpc.com"
    SEPOLIA_RPC_URL: str = "https://ethereum-sepolia-rpc.publicnode.com"
    POLYGON_RPC_URL: str = "https://polygon-rpc.com"
    BNB_RPC_URL: str = "https://bsc-dataseed.binance.org"

    # Supabase Configuration
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None

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
data_dir = BASE_DIR.parent / "data"
data_dir.mkdir(parents=True, exist_ok=True)
address_labels_dir = data_dir / "address_labels"
address_labels_dir.mkdir(parents=True, exist_ok=True)
sample_cases_dir = data_dir / "sample_cases"
sample_cases_dir.mkdir(parents=True, exist_ok=True)
