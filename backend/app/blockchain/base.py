from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

class NormalizedTx(BaseModel):
    transaction_hash: str
    blockchain: str
    block_number: Optional[int] = None
    timestamp: datetime
    from_address: str
    to_address: str
    amount_native: float
    amount_usd_if_available: Optional[float] = None
    gas_used: Optional[float] = None
    gas_fee: Optional[float] = None
    status: str = "SUCCESS"

class BlockchainProvider(ABC):
    def __init__(self, name: str, rpc_url: str):
        self.name = name
        self.rpc_url = rpc_url

    @abstractmethod
    def validate_address(self, address: str) -> bool:
        """Validates if the provided string is a valid Ethereum/EVM address."""
        pass

    @abstractmethod
    def get_latest_block(self) -> Optional[Dict[str, Any]]:
        """Retrieves metadata of the latest mined block."""
        pass

    @abstractmethod
    def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieves raw transaction data by transaction hash."""
        pass

    @abstractmethod
    def get_transaction_receipt(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieves the transaction receipt by transaction hash."""
        pass

    @abstractmethod
    def get_balance(self, address: str) -> Dict[str, Any]:
        """Returns balance details in wei and ether."""
        pass
