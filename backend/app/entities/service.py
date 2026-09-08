import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from web3 import Web3
from app.database.models import AddressLabel, EntityType, ConfidenceLevel, Case, Transaction
from app.entities.schemas import AddressLabelCreate, LabelImportRequest, LabelImportResponse, EntityResolveResponse
from app.entities.repository import AddressLabelRepository
from app.entities.resolver import EntityResolver

DEMO_DATASET_LABELS = [
    {
        "address": "0x28C6c06298d514Db089934071355E5743bf21d60",
        "blockchain": "Ethereum",
        "chain_id": 11155111,
        "entity_type": "EXCHANGE",
        "entity_name": "Binance Hot Wallet",
        "label": "Binance Main Exchange Hot Wallet",
        "source": "DEMO DATASET - Verified Forensic Seed",
        "confidence": "HIGH",
        "verified": True,
        "notes": "Verified exchange deposit/withdrawal hub"
    },
    {
        "address": "0xA090e606E30bD747d4E6245a1517EbE430F0057e",
        "blockchain": "Ethereum",
        "chain_id": 11155111,
        "entity_type": "VASP",
        "entity_name": "Coinbase Custody",
        "label": "Coinbase Institutional Custody VASP",
        "source": "DEMO DATASET - Verified Forensic Seed",
        "confidence": "HIGH",
        "verified": True,
        "notes": "Regulated VASP entity wallet"
    },
    {
        "address": "0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b",
        "blockchain": "Ethereum",
        "chain_id": 11155111,
        "entity_type": "MIXER",
        "entity_name": "Tornado Cash Router",
        "label": "Tornado Cash Anonymizing Contract",
        "source": "DEMO DATASET - Verified Forensic Seed",
        "confidence": "HIGH",
        "verified": True,
        "notes": "Known mixing protocol gateway"
    },
    {
        "address": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "blockchain": "Ethereum",
        "chain_id": 11155111,
        "entity_type": "DEX",
        "entity_name": "Uniswap V3 Router",
        "label": "Uniswap V3 Swap Router Contract",
        "source": "DEMO DATASET - Verified Forensic Seed",
        "confidence": "HIGH",
        "verified": True,
        "notes": "Decentralized automated market maker"
    },
    {
        "address": "0x40ec5B33f54e0E8A33A975908C5BA1c14e5BbbDf",
        "blockchain": "Ethereum",
        "chain_id": 11155111,
        "entity_type": "BRIDGE",
        "entity_name": "Polygon Bridge",
        "label": "Polygon PoS ERC20 Bridge Gateway",
        "source": "DEMO DATASET - Verified Forensic Seed",
        "confidence": "HIGH",
        "verified": True,
        "notes": "Cross-chain asset bridging gateway"
    }
]

class EntityService:
    @staticmethod
    def seed_demo_intel(db: Session) -> int:
        """Seeds demo dataset labels if not already present."""
        seeded = 0
        for item in DEMO_DATASET_LABELS:
            norm = item["address"].lower()
            existing = AddressLabelRepository.get_by_address(
                db, norm, item["blockchain"], item["chain_id"]
            )
            if not existing:
                lbl = AddressLabel(
                    address=norm,
                    blockchain=item["blockchain"],
                    chain_id=item["chain_id"],
                    entity_type=EntityType[item["entity_type"]],
                    entity_name=item["entity_name"],
                    label=item["label"],
                    source=item["source"],
                    confidence=ConfidenceLevel[item["confidence"]],
                    verified=item["verified"],
                    notes=item["notes"],
                    last_verified_at=datetime.datetime.utcnow(),
                    created_at=datetime.datetime.utcnow()
                )
                db.add(lbl)
                seeded += 1
        if seeded > 0:
            db.commit()
        return seeded

    @staticmethod
    def create_or_update_label(db: Session, label_in: AddressLabelCreate) -> AddressLabel:
        if not Web3.is_address(label_in.address):
            raise ValueError(f"Invalid Ethereum address format: '{label_in.address}'")

        norm_addr = label_in.address.lower()
        existing = AddressLabelRepository.get_by_address(
            db, norm_addr, label_in.blockchain, label_in.chain_id
        )

        # Validate entity type enum
        try:
            etype = EntityType[label_in.entity_type.upper()]
        except KeyError:
            etype = EntityType.UNKNOWN

        try:
            conf = ConfidenceLevel[label_in.confidence.upper()]
        except KeyError:
            conf = ConfidenceLevel.HIGH

        if existing:
            existing.entity_name = label_in.entity_name
            existing.entity_type = etype
            existing.label = label_in.label or f"Known {label_in.entity_name}"
            existing.source = label_in.source or "Forensic Database"
            existing.source_url = label_in.source_url
            existing.confidence = conf
            existing.verified = label_in.verified
            existing.notes = label_in.notes
            existing.last_verified_at = datetime.datetime.utcnow()
            existing.updated_at = datetime.datetime.utcnow()
            lbl = existing
        else:
            lbl = AddressLabel(
                address=norm_addr,
                blockchain=label_in.blockchain,
                chain_id=label_in.chain_id,
                entity_name=label_in.entity_name,
                entity_type=etype,
                label=label_in.label or f"Known {label_in.entity_name}",
                source=label_in.source or "Forensic Database",
                source_url=label_in.source_url,
                confidence=conf,
                verified=label_in.verified,
                notes=label_in.notes,
                last_verified_at=datetime.datetime.utcnow(),
                created_at=datetime.datetime.utcnow()
            )
            db.add(lbl)

        db.commit()
        db.refresh(lbl)
        return lbl

    @staticmethod
    def import_labels(db: Session, import_req: LabelImportRequest) -> LabelImportResponse:
        imported = 0
        skipped = 0
        failed = 0
        errors = []

        for item in import_req.labels:
            if not Web3.is_address(item.address):
                failed += 1
                errors.append(f"Invalid address: '{item.address}'")
                continue

            norm = item.address.lower()
            existing = AddressLabelRepository.get_by_address(db, norm, item.blockchain, item.chain_id)
            if existing:
                skipped += 1
                continue

            try:
                try:
                    etype = EntityType[item.entity_type.upper()]
                except KeyError:
                    etype = EntityType.UNKNOWN

                try:
                    conf = ConfidenceLevel[item.confidence.upper()]
                except KeyError:
                    conf = ConfidenceLevel.HIGH

                lbl = AddressLabel(
                    address=norm,
                    blockchain=item.blockchain,
                    chain_id=item.chain_id,
                    entity_name=item.entity_name,
                    entity_type=etype,
                    label=item.label or f"Known {item.entity_name}",
                    source=item.source or import_req.dataset_name,
                    source_url=item.source_url,
                    confidence=conf,
                    verified=item.verified,
                    notes=item.notes,
                    last_verified_at=datetime.datetime.utcnow(),
                    created_at=datetime.datetime.utcnow()
                )
                db.add(lbl)
                imported += 1
            except Exception as e:
                failed += 1
                errors.append(f"Failed importing '{item.address}': {str(e)}")

        if imported > 0:
            db.commit()

        return LabelImportResponse(
            imported_count=imported,
            skipped_duplicates=skipped,
            failed_count=failed,
            errors=errors[:10]
        )

    @staticmethod
    def get_case_entities(db: Session, case_id: str) -> List[EntityResolveResponse]:
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if not case:
            raise ValueError(f"Case '{case_id}' not found.")

        # Find all counterparties from case transactions
        txs = db.query(Transaction).filter(
            (Transaction.case_id == case_id) |
            (Transaction.from_address.ilike(case.suspect_wallet)) |
            (Transaction.to_address.ilike(case.suspect_wallet))
        ).all()

        addrs = set([case.suspect_wallet.lower()])
        for tx in txs:
            if tx.from_address:
                addrs.add(tx.from_address.lower())
            if tx.to_address:
                addrs.add(tx.to_address.lower())

        results = []
        for addr in addrs:
            resolved = EntityResolver.resolve_address(
                db=db,
                address=addr,
                blockchain=case.blockchain or "Ethereum"
            )
            results.append(resolved)

        return results
