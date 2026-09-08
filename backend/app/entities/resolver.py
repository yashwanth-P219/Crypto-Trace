from typing import Optional
from sqlalchemy.orm import Session
from app.entities.repository import AddressLabelRepository
from app.entities.schemas import EntityResolveResponse

class EntityResolver:
    @staticmethod
    def resolve_address(
        db: Session,
        address: str,
        blockchain: str = "Ethereum",
        chain_id: int = 11155111
    ) -> EntityResolveResponse:
        """
        Resolves an Ethereum address against local forensic intel.
        Strictly adheres to: Unlabeled addresses remain UNKNOWN (never fraudulent by default).
        """
        norm_address = address.lower()
        lbl = AddressLabelRepository.get_by_address(
            db=db,
            address=norm_address,
            blockchain=blockchain,
            chain_id=chain_id
        )

        if lbl:
            etype_str = lbl.entity_type.value if hasattr(lbl.entity_type, 'value') else str(lbl.entity_type)
            conf_str = lbl.confidence.value if hasattr(lbl.confidence, 'value') else str(lbl.confidence)
            return EntityResolveResponse(
                address=norm_address,
                blockchain=lbl.blockchain,
                chain_id=lbl.chain_id,
                entity_type=etype_str,
                entity_name=lbl.entity_name,
                label=lbl.label or f"Known {lbl.entity_name}",
                source=lbl.source,
                source_url=lbl.source_url,
                confidence=conf_str,
                verified=bool(lbl.verified),
                is_known=True
            )

        # Default UNKNOWN response
        return EntityResolveResponse(
            address=norm_address,
            blockchain=blockchain,
            chain_id=chain_id,
            entity_type="UNKNOWN",
            entity_name=None,
            label="Unlabeled Wallet",
            source=None,
            source_url=None,
            confidence="LOW",
            verified=False,
            is_known=False
        )
