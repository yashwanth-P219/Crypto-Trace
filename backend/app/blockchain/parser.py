import datetime
from typing import Dict, Any, Optional
from web3 import Web3
from .base import NormalizedTx

class TransactionParser:
    @staticmethod
    def parse_web3_tx(
        tx: Dict[str, Any],
        receipt: Optional[Dict[str, Any]] = None,
        block: Optional[Dict[str, Any]] = None,
        blockchain: str = "Ethereum",
        native_usd_rate: float = 3000.0
    ) -> NormalizedTx:
        tx_hash = tx.get("hash")
        if hasattr(tx_hash, "hex"):
            tx_hash = tx_hash.hex()
        elif isinstance(tx_hash, bytes):
            tx_hash = "0x" + tx_hash.hex()

        from_addr = tx.get("from", "")
        if hasattr(from_addr, "lower"):
            from_addr = Web3.to_checksum_address(from_addr)

        to_addr = tx.get("to") or "0x0000000000000000000000000000000000000000"
        if hasattr(to_addr, "lower"):
            to_addr = Web3.to_checksum_address(to_addr)

        val_wei = tx.get("value", 0)
        amount_native = float(Web3.from_wei(val_wei, "ether"))

        # Timestamp from block
        ts = datetime.datetime.utcnow()
        if block and "timestamp" in block:
            ts = datetime.datetime.utcfromtimestamp(block["timestamp"])

        # Gas calculations
        gas_price = tx.get("gasPrice", 0)
        gas_used = receipt.get("gasUsed") if receipt else tx.get("gas", 21000)
        gas_fee_native = float(Web3.from_wei(gas_price * (gas_used or 21000), "ether"))

        status = "SUCCESS"
        if receipt and "status" in receipt:
            status = "SUCCESS" if receipt["status"] == 1 else "FAILED"

        return NormalizedTx(
            transaction_hash=str(tx_hash),
            blockchain=blockchain,
            block_number=tx.get("blockNumber"),
            timestamp=ts,
            from_address=str(from_addr),
            to_address=str(to_addr),
            amount_native=amount_native,
            amount_usd_if_available=round(amount_native * native_usd_rate, 2),
            gas_used=float(gas_used) if gas_used else None,
            gas_fee=gas_fee_native,
            status=status
        )

    @staticmethod
    def parse_dict(data: Dict[str, Any], blockchain: str = "Ethereum") -> NormalizedTx:
        ts = data.get("timestamp")
        if isinstance(ts, str):
            try:
                ts = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                ts = datetime.datetime.utcnow()
        elif isinstance(ts, (int, float)):
            ts = datetime.datetime.utcfromtimestamp(ts)
        elif not isinstance(ts, datetime.datetime):
            ts = datetime.datetime.utcnow()

        from_addr = data.get("from_address") or data.get("from", "")
        to_addr = data.get("to_address") or data.get("to", "")
        try:
            if Web3.is_address(from_addr):
                from_addr = Web3.to_checksum_address(from_addr)
            if Web3.is_address(to_addr):
                to_addr = Web3.to_checksum_address(to_addr)
        except Exception:
            pass

        amt = float(data.get("amount_native") or data.get("value") or 0.0)
        usd = data.get("amount_usd_if_available")
        if usd is None and amt > 0:
            usd = round(amt * 3000.0, 2)

        return NormalizedTx(
            transaction_hash=str(data.get("transaction_hash") or data.get("hash")),
            blockchain=blockchain,
            block_number=data.get("block_number") or data.get("blockNumber"),
            timestamp=ts,
            from_address=from_addr,
            to_address=to_addr,
            amount_native=amt,
            amount_usd_if_available=usd,
            gas_used=float(data.get("gas_used") or 21000),
            gas_fee=float(data.get("gas_fee") or 0.00042),
            status=str(data.get("status") or "SUCCESS")
        )
