import logging
import httpx
from typing import List, Dict, Any, Optional
from web3 import Web3
from app.config import settings
from .base import BlockchainProvider, NormalizedTx
from .rpc import ResilientRPCClient
from .parser import TransactionParser

logger = logging.getLogger("blockchain.polygon")

class PolygonProvider(BlockchainProvider):
    def __init__(self):
        super().__init__(name="Polygon", rpc_url=settings.POLYGON_RPC_URL)
        self.rpc_client = ResilientRPCClient(self.rpc_url, self.name)
        self.api_key = settings.POLYGONSCAN_API_KEY
        self.explorer_api = "https://api.polygonscan.com/api"

    def validate_address(self, address: str) -> bool:
        if not address or not isinstance(address, str):
            return False
        return Web3.is_address(address)

    def get_latest_block(self) -> Optional[Dict[str, Any]]:
        return self.rpc_client.get_latest_block()

    def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        return self.rpc_client.get_transaction(tx_hash)

    def get_transaction_receipt(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        return self.rpc_client.get_transaction_receipt(tx_hash)

    def get_balance(self, address: str) -> Dict[str, Any]:
        if not self.validate_address(address):
            raise ValueError("Invalid Polygon wallet address")
        checksum = Web3.to_checksum_address(address)
        raw_wei = self.rpc_client.get_raw_balance(checksum)
        balance_native = float(Web3.from_wei(raw_wei, "ether"))
        return {
            "address": checksum,
            "network": "Polygon PoS",
            "balance": raw_wei,
            "balance_eth": balance_native
        }
