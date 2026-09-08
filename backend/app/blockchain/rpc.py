import logging
import time
from typing import Optional, Dict, Any, List
from web3 import Web3, HTTPProvider
from web3.exceptions import BlockNotFound, TransactionNotFound

logger = logging.getLogger("blockchain.rpc")

class ResilientRPCClient:
    """
    Resilient Web3 RPC client with retry logic, fallback endpoints,
    timeout handling, and graceful error recovery.
    """
    def __init__(
        self,
        primary_rpc_url: str,
        chain_name: str = "Ethereum Sepolia",
        fallback_rpc_urls: Optional[List[str]] = None,
        max_retries: int = 3,
        timeout: int = 8
    ):
        self.chain_name = chain_name
        self.primary_rpc_url = primary_rpc_url
        self.fallback_rpc_urls = fallback_rpc_urls or []
        self.all_rpc_urls = [primary_rpc_url] + [u for u in self.fallback_rpc_urls if u != primary_rpc_url]
        self.max_retries = max_retries
        self.timeout = timeout
        self.active_rpc_url = primary_rpc_url
        self.w3 = self._create_web3(self.active_rpc_url)

    def _create_web3(self, url: str) -> Web3:
        try:
            return Web3(HTTPProvider(url, request_kwargs={"timeout": self.timeout}))
        except Exception as e:
            logger.error(f"Failed to initialize Web3 provider for URL {url}: {e}")
            return Web3()

    def is_connected(self) -> bool:
        """Checks if current RPC connection is alive; falls back to secondary endpoints if available."""
        for url in self.all_rpc_urls:
            try:
                w3_instance = self._create_web3(url) if url != self.active_rpc_url else self.w3
                if w3_instance.is_connected():
                    if url != self.active_rpc_url:
                        logger.info(f"Switched active RPC from {self.active_rpc_url} to working fallback {url}")
                        self.active_rpc_url = url
                        self.w3 = w3_instance
                    return True
            except Exception as e:
                logger.warning(f"Connection check failed for {url} ({self.chain_name}): {e}")
        return False

    def get_latest_block_number(self) -> Optional[int]:
        """Returns the current highest block number on chain."""
        for attempt in range(self.max_retries):
            try:
                if not self.w3.is_connected():
                    self.is_connected()
                return self.w3.eth.block_number
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed getting block number on {self.chain_name}: {e}")
                time.sleep(0.5 * (attempt + 1))
        return None

    def get_latest_block(self) -> Optional[Dict[str, Any]]:
        """Retrieves full metadata of the latest mined block."""
        for attempt in range(self.max_retries):
            try:
                block = self.w3.eth.get_block('latest', full_transactions=False)
                return dict(block)
            except BlockNotFound:
                return None
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} get_latest_block failed on {self.chain_name}: {e}")
                time.sleep(0.5 * (attempt + 1))
        return None

    def get_raw_balance(self, address: str) -> int:
        """Retrieves raw account balance in Wei."""
        try:
            checksum = Web3.to_checksum_address(address)
        except Exception:
            raise ValueError(f"Invalid Ethereum address: {address}")

        for attempt in range(self.max_retries):
            try:
                wei = self.w3.eth.get_balance(checksum)
                return int(wei)
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} get_balance failed on {self.chain_name} for {address}: {e}")
                time.sleep(0.5 * (attempt + 1))
        return 0

    def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieves transaction object by hash."""
        for attempt in range(self.max_retries):
            try:
                tx = self.w3.eth.get_transaction(tx_hash)
                return dict(tx)
            except TransactionNotFound:
                logger.info(f"Transaction {tx_hash} not found on {self.chain_name}")
                return None
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} get_transaction failed for {tx_hash}: {e}")
                time.sleep(0.5 * (attempt + 1))
        return None

    def get_transaction_receipt(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieves transaction receipt (status, gasUsed, logs)."""
        for attempt in range(self.max_retries):
            try:
                receipt = self.w3.eth.get_transaction_receipt(tx_hash)
                return dict(receipt)
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} get_receipt failed for {tx_hash}: {e}")
                time.sleep(0.5 * (attempt + 1))
        return None

    def get_block(self, block_identifier: Any) -> Optional[Dict[str, Any]]:
        """Retrieves block by number or hash."""
        try:
            block = self.w3.eth.get_block(block_identifier, full_transactions=False)
            return dict(block)
        except BlockNotFound:
            return None
        except Exception as e:
            logger.warning(f"Failed to retrieve block {block_identifier}: {e}")
            return None
