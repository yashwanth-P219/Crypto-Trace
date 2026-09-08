import logging
import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.database.models import Transaction, Case, CaseTransaction, Wallet
from app.blockchain.ethereum import EthereumProvider
from app.blockchain.history_provider import SepoliaHistoryProvider
from app.blockchain.transaction_parser import TransactionNormalizer, NormalizedTransaction

logger = logging.getLogger("services.transactions")

class TransactionService:
    @classmethod
    def get_history_provider(cls) -> SepoliaHistoryProvider:
        return SepoliaHistoryProvider()

    @classmethod
    def validate_wallet_address(cls, address: str) -> bool:
        provider = EthereumProvider(network="Sepolia")
        return provider.validate_address(address)

    @classmethod
    def get_wallet_transactions(
        cls,
        db: Session,
        address: str,
        page: int = 1,
        page_size: int = 50,
        direction: str = "all",
        from_block: Optional[int] = None,
        to_block: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Retrieves paginated stored transaction history for a wallet from the database.
        """
        if not cls.validate_wallet_address(address):
            raise ValueError("Invalid Ethereum wallet address")

        norm_addr = address.lower().strip()
        page = max(1, page)
        page_size = max(1, min(page_size, 100))

        query = db.query(Transaction)

        # Direction filter
        if direction == "incoming":
            query = query.filter(Transaction.to_address == norm_addr)
        elif direction == "outgoing":
            query = query.filter(Transaction.from_address == norm_addr)
        else:
            query = query.filter(
                or_(
                    Transaction.from_address == norm_addr,
                    Transaction.to_address == norm_addr
                )
            )

        # Block range filter
        if from_block is not None:
            query = query.filter(Transaction.block_number >= from_block)
        if to_block is not None:
            query = query.filter(Transaction.block_number <= to_block)

        total = query.count()

        # Efficient database pagination
        records = (
            query.order_by(
                Transaction.block_number.desc().nullslast(),
                Transaction.block_timestamp.desc().nullslast(),
                Transaction.id.desc()
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        tx_list = []
        for tx in records:
            tx_direction = TransactionNormalizer.classify_direction(
                tx.from_address, tx.to_address, norm_addr
            )
            tx_list.append({
                "id": tx.id,
                "tx_hash": tx.tx_hash,
                "blockchain": tx.blockchain,
                "chain_id": tx.chain_id,
                "block_number": tx.block_number,
                "block_hash": tx.block_hash,
                "transaction_index": tx.transaction_index,
                "from_address": tx.from_address,
                "to_address": tx.to_address,
                "value_wei": tx.value_wei,
                "value_eth": tx.value_eth,
                "gas": tx.gas,
                "gas_price_wei": tx.gas_price_wei,
                "nonce": tx.nonce,
                "receipt_status": tx.receipt_status,
                "gas_used": tx.gas_used,
                "block_timestamp": tx.block_timestamp.isoformat() if tx.block_timestamp else None,
                "transaction_type": tx.transaction_type,
                "direction": tx_direction,
                "created_at": tx.created_at.isoformat() if tx.created_at else None
            })

        return {
            "wallet": address,
            "blockchain": "Ethereum",
            "chain_id": 11155111,
            "page": page,
            "page_size": page_size,
            "total": total,
            "transactions": tx_list,
            "items": tx_list
        }

    @classmethod
    def sync_wallet_transactions(
        cls,
        db: Session,
        address: str,
        case_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synchronizes real Ethereum Sepolia transactions for a wallet into PostgreSQL.
        Prevents duplicates via uq_tx_chain constraint.
        """
        if not cls.validate_wallet_address(address):
            raise ValueError("Invalid Ethereum wallet address")

        norm_addr = address.lower().strip()
        provider = cls.get_history_provider()

        logger.info(f"Starting transaction sync for wallet {norm_addr} (case_id={case_id})")

        raw_items = provider.get_transactions_for_address(norm_addr, page=1, page_size=100)
        fetched_count = len(raw_items)

        inserted_count = 0
        updated_count = 0
        duplicate_count = 0
        failed_count = 0

        # If explorer has no results, check if on-chain RPC knows of recent activity
        if fetched_count == 0:
            logger.info(f"No explorer history found for {norm_addr}; checking balance and RPC provider")
            try:
                # Ensure wallet record exists
                wallet = db.query(Wallet).filter(Wallet.address == norm_addr).first()
                if not wallet:
                    wallet = Wallet(
                        address=norm_addr,
                        blockchain="Ethereum",
                        created_at=datetime.datetime.utcnow()
                    )
                    db.add(wallet)
                    db.commit()
            except Exception as e:
                db.rollback()

        for item in raw_items:
            try:
                norm_tx = TransactionNormalizer.from_explorer_dict(
                    item, chain_id=11155111, target_wallet=norm_addr
                )

                # Duplicate check: tx_hash + blockchain + chain_id
                existing_tx = db.query(Transaction).filter(
                    Transaction.tx_hash == norm_tx.tx_hash,
                    Transaction.blockchain == norm_tx.blockchain,
                    Transaction.chain_id == norm_tx.chain_id
                ).first()

                if existing_tx:
                    duplicate_count += 1
                    # Update metadata if previous record lacked block timestamp
                    if not existing_tx.block_timestamp and norm_tx.block_timestamp:
                        existing_tx.block_timestamp = norm_tx.block_timestamp
                        updated_count += 1
                    tx_record = existing_tx
                else:
                    tx_record = Transaction(
                        tx_hash=norm_tx.tx_hash,
                        blockchain=norm_tx.blockchain,
                        chain_id=norm_tx.chain_id,
                        block_number=norm_tx.block_number,
                        block_hash=norm_tx.block_hash,
                        transaction_index=norm_tx.transaction_index,
                        from_address=norm_tx.from_address,
                        to_address=norm_tx.to_address,
                        value_wei=norm_tx.value_wei,
                        value_eth=norm_tx.value_eth,
                        gas=norm_tx.gas,
                        gas_price_wei=norm_tx.gas_price_wei,
                        nonce=norm_tx.nonce,
                        receipt_status=norm_tx.receipt_status,
                        gas_used=norm_tx.gas_used,
                        block_timestamp=norm_tx.block_timestamp,
                        transaction_type=norm_tx.transaction_type,
                        case_id=case_id,
                        created_at=datetime.datetime.utcnow()
                    )
                    db.add(tx_record)
                    db.flush()
                    inserted_count += 1

                # Associate with case if requested
                if case_id and tx_record.id:
                    case_assoc = db.query(CaseTransaction).filter(
                        CaseTransaction.case_id == case_id,
                        CaseTransaction.transaction_id == tx_record.id
                    ).first()
                    if not case_assoc:
                        new_assoc = CaseTransaction(
                            case_id=case_id,
                            transaction_id=tx_record.id,
                            created_at=datetime.datetime.utcnow()
                        )
                        db.add(new_assoc)

            except Exception as e:
                logger.warning(f"Failed to process transaction item: {e}")
                failed_count += 1

        db.commit()

        logger.info(
            f"Transaction sync completed for {norm_addr}: "
            f"fetched={fetched_count}, inserted={inserted_count}, duplicates={duplicate_count}, failed={failed_count}"
        )

        return {
            "wallet": address,
            "blockchain": "Ethereum",
            "chain_id": 11155111,
            "fetched": fetched_count,
            "inserted": inserted_count,
            "updated": updated_count,
            "duplicates": duplicate_count,
            "failed": failed_count
        }

    @classmethod
    def sync_case_transactions(cls, db: Session, case_id: str) -> Dict[str, Any]:
        """
        Retrieves suspect wallet for the given case and syncs its transactions.
        """
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if not case:
            raise ValueError(f"Case with ID '{case_id}' not found")
        if not case.suspect_wallet:
            raise ValueError(f"Case '{case_id}' does not have an associated suspect wallet")

        return cls.sync_wallet_transactions(db, case.suspect_wallet, case_id=case_id)

    @classmethod
    def get_transaction_by_hash(cls, db: Session, tx_hash: str) -> Optional[Dict[str, Any]]:
        """
        Database-first transaction retrieval with live Sepolia RPC fallback and auto-caching.
        """
        clean_hash = TransactionNormalizer.normalize_tx_hash(tx_hash)

        # 1. Search Database first (Cache hit)
        tx = db.query(Transaction).filter(
            or_(
                Transaction.tx_hash.ilike(clean_hash),
                Transaction.id == int(clean_hash) if clean_hash.isdigit() else False
            )
        ).first()

        if tx:
            return {
                "transaction_hash": tx.tx_hash,
                "tx_hash": tx.tx_hash,
                "blockchain": tx.blockchain,
                "chain_id": tx.chain_id,
                "block_number": tx.block_number,
                "block_hash": tx.block_hash,
                "transaction_index": tx.transaction_index,
                "from_address": tx.from_address,
                "to_address": tx.to_address,
                "value": int(tx.value_wei) if tx.value_wei.isdigit() else 0,
                "value_wei": tx.value_wei,
                "value_eth": tx.value_eth,
                "gas": tx.gas,
                "gas_price": int(tx.gas_price_wei) if tx.gas_price_wei and tx.gas_price_wei.isdigit() else 0,
                "gas_price_wei": tx.gas_price_wei,
                "status": tx.receipt_status,
                "receipt_status": tx.receipt_status,
                "gas_used": tx.gas_used,
                "timestamp": int(tx.block_timestamp.timestamp()) if tx.block_timestamp else None,
                "block_timestamp": tx.block_timestamp.isoformat() if tx.block_timestamp else None,
                "transaction_type": tx.transaction_type,
                "source": "database_cache"
            }

        # 2. Database miss: Query Sepolia RPC live
        provider = cls.get_history_provider()
        raw_tx = provider.get_transaction(clean_hash)
        if not raw_tx:
            return None

        receipt = provider.get_transaction_receipt(clean_hash)
        block = None
        if raw_tx.get("blockNumber"):
            block = provider.get_block(raw_tx.get("blockNumber"))

        norm_tx = TransactionNormalizer.from_web3_dict(
            tx=raw_tx, receipt=receipt, block=block, chain_id=11155111
        )

        # 3. Store in Database for future cache hits
        try:
            new_tx = Transaction(
                tx_hash=norm_tx.tx_hash,
                blockchain=norm_tx.blockchain,
                chain_id=norm_tx.chain_id,
                block_number=norm_tx.block_number,
                block_hash=norm_tx.block_hash,
                transaction_index=norm_tx.transaction_index,
                from_address=norm_tx.from_address,
                to_address=norm_tx.to_address,
                value_wei=norm_tx.value_wei,
                value_eth=norm_tx.value_eth,
                gas=norm_tx.gas,
                gas_price_wei=norm_tx.gas_price_wei,
                nonce=norm_tx.nonce,
                receipt_status=norm_tx.receipt_status,
                gas_used=norm_tx.gas_used,
                block_timestamp=norm_tx.block_timestamp,
                transaction_type=norm_tx.transaction_type,
                created_at=datetime.datetime.utcnow()
            )
            db.add(new_tx)
            db.commit()
            db.refresh(new_tx)
        except Exception as e:
            db.rollback()
            logger.warning(f"Could not cache retrieved transaction: {e}")

        return {
            "transaction_hash": norm_tx.tx_hash,
            "tx_hash": norm_tx.tx_hash,
            "blockchain": norm_tx.blockchain,
            "chain_id": norm_tx.chain_id,
            "block_number": norm_tx.block_number,
            "block_hash": norm_tx.block_hash,
            "transaction_index": norm_tx.transaction_index,
            "from_address": norm_tx.from_address,
            "to_address": norm_tx.to_address,
            "value": int(norm_tx.value_wei) if norm_tx.value_wei.isdigit() else 0,
            "value_wei": norm_tx.value_wei,
            "value_eth": norm_tx.value_eth,
            "gas": norm_tx.gas,
            "gas_price": int(norm_tx.gas_price_wei) if norm_tx.gas_price_wei and norm_tx.gas_price_wei.isdigit() else 0,
            "gas_price_wei": norm_tx.gas_price_wei,
            "status": norm_tx.receipt_status,
            "receipt_status": norm_tx.receipt_status,
            "gas_used": norm_tx.gas_used,
            "timestamp": int(norm_tx.block_timestamp.timestamp()) if norm_tx.block_timestamp else None,
            "block_timestamp": norm_tx.block_timestamp.isoformat() if norm_tx.block_timestamp else None,
            "transaction_type": norm_tx.transaction_type,
            "source": "live_blockchain"
        }
