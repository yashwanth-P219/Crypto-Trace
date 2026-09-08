import logging
import re
from typing import List, Dict, Any, Optional
from web3 import Web3
from app.config import settings
from .base import BlockchainProvider, NormalizedTx
from .rpc import ResilientRPCClient
from .parser import TransactionParser

logger = logging.getLogger("blockchain.ethereum")

class EthereumProvider(BlockchainProvider):
    """
    Ethereum Blockchain Provider supporting Sepolia Testnet as primary
    and Ethereum Mainnet (read-only) with resilient RPC failover.
    """
    def __init__(self, network: str = "Sepolia"):
        is_sepolia = network.lower() == "sepolia"
        primary_rpc = settings.SEPOLIA_RPC_URL if is_sepolia else settings.ETHEREUM_RPC_URL

        # Reliable public fallbacks for Sepolia
        fallbacks = (
            [
                "https://ethereum-sepolia-rpc.publicnode.com",
                "https://1rpc.io/sepolia",
                "https://rpc2.sepolia.org"
            ]
            if is_sepolia
            else [
                "https://eth.llamarpc.com",
                "https://rpc.ankr.com/eth",
                "https://1rpc.io/eth"
            ]
        )

        chain_name = f"Ethereum {network.capitalize()}"
        super().__init__(name=chain_name, rpc_url=primary_rpc)
        self.network = f"Ethereum {network.capitalize()}"
        self.rpc_client = ResilientRPCClient(
            primary_rpc_url=primary_rpc,
            chain_name=self.name,
            fallback_rpc_urls=fallbacks,
            max_retries=3,
            timeout=8
        )

    def validate_address(self, address: str) -> bool:
        """
        Validates whether the given string is a valid Ethereum/EVM hex address.
        Must be 42 characters starting with 0x and containing valid hex digits.
        """
        if not address or not isinstance(address, str):
            return False
        addr = address.strip()
        if not re.match(r"^0x[a-fA-F0-9]{40}$", addr):
            return False
        return Web3.is_address(addr)

    def get_latest_block(self) -> Optional[Dict[str, Any]]:
        """Retrieves the latest mined block details."""
        return self.rpc_client.get_latest_block()

    def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieves transaction data by hash."""
        if not tx_hash or not re.match(r"^0x[a-fA-F0-9]{64}$", tx_hash.strip()):
            return None
        return self.rpc_client.get_transaction(tx_hash.strip())

    def get_transaction_receipt(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieves transaction receipt data by hash."""
        if not tx_hash or not re.match(r"^0x[a-fA-F0-9]{64}$", tx_hash.strip()):
            return None
        return self.rpc_client.get_transaction_receipt(tx_hash.strip())

    def get_balance(self, address: str) -> Dict[str, Any]:
        """
        Retrieves balance in both raw Wei and Ether.
        Raises ValueError if address is invalid.
        """
        if not self.validate_address(address):
            raise ValueError("Invalid Ethereum wallet address")

        checksum = Web3.to_checksum_address(address.strip())
        raw_wei = self.rpc_client.get_raw_balance(checksum)
        balance_eth = float(Web3.from_wei(raw_wei, "ether"))

        return {
            "address": checksum,
            "network": self.network,
            "balance": raw_wei,
            "balance_eth": balance_eth
        }

    def get_status(self) -> Dict[str, Any]:
        """Returns connection status and latest block number."""
        is_conn = self.rpc_client.is_connected()
        latest_block = self.rpc_client.get_latest_block_number() if is_conn else None
        return {
            "connected": is_conn,
            "network": self.network,
            "latest_block": latest_block
        }
