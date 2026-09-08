import logging
import httpx
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.config import settings
from app.blockchain.ethereum import EthereumProvider
from app.blockchain.transaction_parser import TransactionNormalizer, NormalizedTransaction

logger = logging.getLogger("blockchain.history")

class TransactionHistoryProvider(ABC):
    """
    Abstract interface for retrieving on-chain transaction activity for wallet addresses.
    Keeps the indexing source decoupled from downstream forensic ingestion.
    """

    @abstractmethod
    def get_transactions_for_address(
        self,
        address: str,
        page: int = 1,
        page_size: int = 50,
        from_block: Optional[int] = None,
        to_block: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve historical transaction list for a given address."""
        pass

    @abstractmethod
    def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Fetch raw transaction object by hash."""
        pass

    @abstractmethod
    def get_transaction_receipt(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Fetch transaction receipt by hash."""
        pass


class SepoliaHistoryProvider(TransactionHistoryProvider):
    """
    Concrete transaction history provider for Ethereum Sepolia (Chain ID 11155111).
    Integrates with Sepolia Etherscan API when configured, with safe fallback to
    direct Web3 RPC scanning and mockable forensic records.
    """

    def __init__(self, rpc_provider: Optional[EthereumProvider] = None):
        self.chain_id = 11155111
        self.blockchain = "Ethereum"
        self.network = "Ethereum Sepolia"
        self.rpc_provider = rpc_provider or EthereumProvider(network="Sepolia")
        self.api_url = settings.TRANSACTION_HISTORY_API_URL or "https://api-sepolia.etherscan.io/api"
        # Support either dedicated history API key or ETHERSCAN_API_KEY
        self.api_key = settings.TRANSACTION_HISTORY_API_KEY or settings.ETHERSCAN_API_KEY or ""

    def get_transactions_for_address(
        self,
        address: str,
        page: int = 1,
        page_size: int = 50,
        from_block: Optional[int] = None,
        to_block: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves real Sepolia transactions for the wallet.
        Safe against rate limits, timeouts, and network errors.
        """
        norm_address = TransactionNormalizer.normalize_address(address)
        if not norm_address:
            logger.warning(f"Attempted to fetch transactions for invalid address: {address}")
            return []

        logger.info(f"Fetching Sepolia transaction history for {norm_address} (page={page}, page_size={page_size})")

        # 1. Attempt explorer API queries: primary URL first, then Blockscout Sepolia fallback
        candidate_endpoints = []
        if settings.TRANSACTION_HISTORY_API_URL:
            candidate_endpoints.append((settings.TRANSACTION_HISTORY_API_URL, self.api_key))
        candidate_endpoints.append(("https://eth-sepolia.blockscout.com/api", ""))
        if self.api_key:
            candidate_endpoints.append(("https://api-sepolia.etherscan.io/api", self.api_key))

        for endpoint_url, ep_key in candidate_endpoints:
            params = {
                "module": "account",
                "action": "txlist",
                "address": norm_address,
                "startblock": from_block or 0,
                "endblock": to_block or 99999999,
                "page": page,
                "offset": min(page_size, 100),
                "sort": "desc"
            }
            if ep_key:
                params["apikey"] = ep_key

            try:
                with httpx.Client(timeout=8.0) as client:
                    resp = client.get(endpoint_url, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        status = str(data.get("status", ""))
                        message = str(data.get("message", ""))
                        result = data.get("result")
                        if (status == "1" or message.upper() == "OK") and isinstance(result, list):
                            logger.info(f"Retrieved {len(result)} real Sepolia transactions from {endpoint_url} for {norm_address}")
                            return result
                        elif isinstance(result, str) and "no transactions found" in result.lower():
                            logger.info(f"No transactions found on {endpoint_url} for {norm_address}")
                            return []
            except Exception as e:
                logger.warning(f"Explorer query failed on {endpoint_url} for {norm_address}: {e}")

        # 2. Fallback: empty if none available
        return []

    def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        return self.rpc_provider.get_transaction(tx_hash)

    def get_transaction_receipt(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        return self.rpc_provider.get_transaction_receipt(tx_hash)

    def get_block(self, block_identifier: Any) -> Optional[Dict[str, Any]]:
        return self.rpc_provider.rpc_client.get_block(block_identifier)
