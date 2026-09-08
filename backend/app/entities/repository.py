from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database.models import AddressLabel

class AddressLabelRepository:
    @staticmethod
    def get_by_address(
        db: Session,
        address: str,
        blockchain: str = "Ethereum",
        chain_id: int = 11155111
    ) -> Optional[AddressLabel]:
        norm = address.lower()
        return db.query(AddressLabel).filter(
            AddressLabel.address.ilike(norm),
            AddressLabel.blockchain.ilike(blockchain),
            AddressLabel.chain_id == chain_id
        ).first()

    @staticmethod
    def search_labels(
        db: Session,
        query_str: str,
        limit: int = 50
    ) -> List[AddressLabel]:
        q = f"%{query_str.lower()}%"
        return db.query(AddressLabel).filter(
            or_(
                AddressLabel.address.ilike(q),
                AddressLabel.entity_name.ilike(q),
                AddressLabel.label.ilike(q)
            )
        ).limit(limit).all()

    @staticmethod
    def get_all(db: Session, limit: int = 100) -> List[AddressLabel]:
        return db.query(AddressLabel).order_by(AddressLabel.entity_name.asc()).limit(limit).all()
