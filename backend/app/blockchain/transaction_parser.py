import re
import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from web3 import Web3

class NormalizedTransaction(BaseModel):
    tx_hash: str
    blockchain: str = "Ethereum"
    chain_id: int = 11155111
    block_number: Optional[int] = None
    block_hash: Optional[str] = None
    transaction_index: Optional[int] = None
    from_address: str
    to_address: Optional[str] = None
    value_wei: str = "0"
    value_eth: float = 0.0
    gas: int = 21000
    gas_price_wei: Optional[str] = None
    nonce: Optional[int] = None
    receipt_status: str = "SUCCESS"
    gas_used: Optional[int] = None
    block_timestamp: Optional[datetime.datetime] = None
    transaction_type: str = "native_transfer"
    direction: Optional[str] = None


class TransactionNormalizer:
    """
    Standardizes raw transaction payloads from Web3 JSON-RPC nodes or block explorer
    APIs into an immutable, forensic-grade normalized schema.
    """

    @staticmethod
    def normalize_address(address: Optional[str]) -> Optional[str]:
        if not address or not isinstance(address, str):
            return None
        clean = address.strip().lower()
        if re.match(r"^0x[a-f0-9]{40}$", clean):
            return clean
        return clean

    @staticmethod
    def normalize_tx_hash(tx_hash: Any) -> str:
        if hasattr(tx_hash, "hex"):
            val = tx_hash.hex()
        elif isinstance(tx_hash, bytes):
            val = "0x" + tx_hash.hex()
        else:
            val = str(tx_hash).strip()
        if not val.startswith("0x"):
            val = "0x" + val
        return val.lower()

    @staticmethod
    def classify_type(input_data: Optional[str]) -> str:
        if input_data and input_data not in ("0x", "0x0", "", None):
            return "contract_interaction"
        return "native_transfer"

    @staticmethod
    def classify_direction(from_addr: str, to_addr: Optional[str], target_wallet: Optional[str]) -> str:
        if not target_wallet:
            return "unknown"
        norm_target = target_wallet.lower().strip()
        norm_from = (from_addr or "").lower().strip()
        norm_to = (to_addr or "").lower().strip()

        if norm_from == norm_target:
            return "outgoing"
        elif norm_to == norm_target:
            return "incoming"
        return "unknown"

    @classmethod
    def from_web3_dict(
        cls,
        tx: Dict[str, Any],
        receipt: Optional[Dict[str, Any]] = None,
        block: Optional[Dict[str, Any]] = None,
        chain_id: int = 11155111,
        target_wallet: Optional[str] = None
    ) -> NormalizedTransaction:
        tx_hash = cls.normalize_tx_hash(tx.get("hash"))
        from_addr = cls.normalize_address(tx.get("from")) or "0x0000000000000000000000000000000000000000"
        to_addr = cls.normalize_address(tx.get("to"))

        val_raw = tx.get("value", 0)
        if isinstance(val_raw, (int, str)):
            val_wei_str = str(int(val_raw))
        else:
            val_wei_str = "0"

        val_wei_int = int(val_wei_str)
        val_eth = float(Web3.from_wei(val_wei_int, "ether"))

        gas = int(tx.get("gas", 21000) or 21000)
        gas_price = tx.get("gasPrice")
        gas_price_str = str(int(gas_price)) if gas_price is not None else None

        receipt_status = "SUCCESS"
        gas_used = None
        if receipt:
            if "status" in receipt:
                receipt_status = "SUCCESS" if receipt["status"] == 1 else "FAILED"
            if "gasUsed" in receipt:
                gas_used = int(receipt["gasUsed"])

        # Timestamp from block
        block_ts = None
        if block and "timestamp" in block:
            try:
                block_ts = datetime.datetime.fromtimestamp(block["timestamp"], datetime.UTC)
            except Exception:
                block_ts = datetime.datetime.utcnow()

        block_hash = tx.get("blockHash")
        block_hash_str = cls.normalize_tx_hash(block_hash) if block_hash else None

        input_payload = tx.get("input")
        if hasattr(input_payload, "hex"):
            input_payload = input_payload.hex()
        elif isinstance(input_payload, bytes):
            input_payload = "0x" + input_payload.hex()

        tx_type = cls.classify_type(input_payload)
        direction = cls.classify_direction(from_addr, to_addr, target_wallet)

        return NormalizedTransaction(
            tx_hash=tx_hash,
            blockchain="Ethereum",
            chain_id=chain_id,
            block_number=tx.get("blockNumber"),
            block_hash=block_hash_str,
            transaction_index=tx.get("transactionIndex"),
            from_address=from_addr,
            to_address=to_addr,
            value_wei=val_wei_str,
            value_eth=val_eth,
            gas=gas,
            gas_price_wei=gas_price_str,
            nonce=tx.get("nonce"),
            receipt_status=receipt_status,
            gas_used=gas_used or gas,
            block_timestamp=block_ts,
            transaction_type=tx_type,
            direction=direction
        )

    @classmethod
    def from_explorer_dict(
        cls,
        data: Dict[str, Any],
        chain_id: int = 11155111,
        target_wallet: Optional[str] = None
    ) -> NormalizedTransaction:
        tx_hash = cls.normalize_tx_hash(data.get("hash") or data.get("transaction_hash"))
        from_addr = cls.normalize_address(data.get("from") or data.get("from_address")) or ""
        to_addr = cls.normalize_address(data.get("to") or data.get("to_address"))

        val_raw = data.get("value", "0")
        try:
            val_wei_int = int(val_raw)
            val_wei_str = str(val_wei_int)
            val_eth = float(Web3.from_wei(val_wei_int, "ether"))
        except Exception:
            val_wei_str = "0"
            val_eth = 0.0

        gas = int(data.get("gas") or 21000)
        gas_used = int(data.get("gasUsed") or data.get("gas_used") or 21000)
        gas_price = data.get("gasPrice") or data.get("gas_price_wei")
        gas_price_str = str(int(gas_price)) if gas_price else None

        # Status: Etherscan uses isError='0' or txreceipt_status='1'
        receipt_status = "SUCCESS"
        if data.get("isError") == "1" or data.get("txreceipt_status") == "0":
            receipt_status = "FAILED"
        elif "status" in data:
            receipt_status = "SUCCESS" if str(data["status"]).upper() in ("1", "SUCCESS") else "FAILED"

        block_ts = None
        ts_val = data.get("timeStamp") or data.get("timestamp") or data.get("block_timestamp")
        if ts_val:
            try:
                if isinstance(ts_val, (int, float)) or (isinstance(ts_val, str) and ts_val.isdigit()):
                    block_ts = datetime.datetime.fromtimestamp(int(ts_val), datetime.UTC)
                elif isinstance(ts_val, str):
                    block_ts = datetime.datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
            except Exception:
                block_ts = datetime.datetime.utcnow()

        input_payload = data.get("input") or data.get("input_data")
        tx_type = cls.classify_type(input_payload)
        direction = cls.classify_direction(from_addr, to_addr, target_wallet)

        return NormalizedTransaction(
            tx_hash=tx_hash,
            blockchain="Ethereum",
            chain_id=chain_id,
            block_number=int(data.get("blockNumber")) if data.get("blockNumber") else None,
            block_hash=cls.normalize_tx_hash(data.get("blockHash")) if data.get("blockHash") else None,
            transaction_index=int(data.get("transactionIndex")) if data.get("transactionIndex") else None,
            from_address=from_addr,
            to_address=to_addr,
            value_wei=val_wei_str,
            value_eth=val_eth,
            gas=gas,
            gas_price_wei=gas_price_str,
            nonce=int(data.get("nonce")) if data.get("nonce") else None,
            receipt_status=receipt_status,
            gas_used=gas_used,
            block_timestamp=block_ts,
            transaction_type=tx_type,
            direction=direction
        )
