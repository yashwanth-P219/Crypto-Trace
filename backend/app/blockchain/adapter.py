from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from web3 import Web3
from app.config import settings

class BlockchainAdapter(ABC):
    def __init__(self, chain_id: int, name: str, symbol: str, is_evm: bool = True):
        self.chain_id = chain_id
        self.name = name
        self.symbol = symbol
        self.is_evm = is_evm

    @abstractmethod
    def validate_address(self, address: str) -> bool:
        pass

    @abstractmethod
    def normalize_address(self, address: str) -> str:
        pass

    @abstractmethod
    def get_balance(self, address: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_latest_block_number(self) -> int:
        pass

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "name": self.name,
            "symbol": self.symbol,
            "is_evm": self.is_evm
        }

class EVMAdapter(BlockchainAdapter):
    def __init__(self, chain_id: int, name: str, symbol: str, rpc_url: Optional[str] = None):
        super().__init__(chain_id=chain_id, name=name, symbol=symbol, is_evm=True)
        self.rpc_url = rpc_url or settings.SEPOLIA_RPC_URL
        self._w3 = None

    @property
    def w3(self):
        if self._w3 is None:
            self._w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        return self._w3

    def validate_address(self, address: str) -> bool:
        if not address or not isinstance(address, str):
            return False
        return Web3.is_address(address)

    def normalize_address(self, address: str) -> str:
        if not self.validate_address(address):
            raise ValueError(f"Invalid address format for {self.name}: {address}")
        return Web3.to_checksum_address(address)

    def get_balance(self, address: str) -> Dict[str, Any]:
        norm = self.normalize_address(address)
        try:
            if self.w3.is_connected():
                wei = self.w3.eth.get_balance(norm)
                return {
                    "address": norm,
                    "chain_id": self.chain_id,
                    "chain_name": self.name,
                    "balance_wei": str(wei),
                    "balance_native": float(Web3.from_wei(wei, 'ether')),
                    "symbol": self.symbol
                }
        except Exception:
            pass
        return {
            "address": norm,
            "chain_id": self.chain_id,
            "chain_name": self.name,
            "balance_wei": "0",
            "balance_native": 0.0,
            "symbol": self.symbol
        }

    def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        try:
            if self.w3.is_connected():
                tx = self.w3.eth.get_transaction(tx_hash)
                receipt = self.w3.eth.get_transaction_receipt(tx_hash)
                return {
                    "tx_hash": tx_hash,
                    "chain_id": self.chain_id,
                    "from_address": tx["from"],
                    "to_address": tx["to"],
                    "value_native": float(Web3.from_wei(tx["value"], 'ether')),
                    "block_number": tx["blockNumber"],
                    "status": "SUCCESS" if receipt.get("status", 1) == 1 else "FAILED"
                }
        except Exception:
            pass
        return None

    def get_latest_block_number(self) -> int:
        try:
            if self.w3.is_connected():
                return self.w3.eth.block_number
        except Exception:
            pass
        return 7000000
