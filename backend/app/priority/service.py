import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.models import (
    Case, Transaction, AddressLabel, AnalysisPattern,
    RiskAssessmentRecord, PriorityItem
)
from app.graph.graph_service import GraphService
from app.priority.engine import PriorityCalculationEngine
from app.priority.schemas import PriorityItemResponse, PriorityQueueResponse

class PriorityService:
    @staticmethod
    def prioritize_wallet(
        db: Session,
        wallet_address: str,
        case_id: Optional[str] = None,
        max_hops: int = 3,
        persist: bool = True
    ) -> List[PriorityItem]:
        norm_wallet = wallet_address.lower().strip()

        # 1. Fetch risk assessment if available
        risk_record = db.query(RiskAssessmentRecord).filter(
            RiskAssessmentRecord.wallet_address.ilike(norm_wallet)
        ).order_by(desc(RiskAssessmentRecord.created_at)).first()
        risk_score = risk_record.risk_score if risk_record else 0.0

        # 2. Fetch analysis patterns
        pat_query = db.query(AnalysisPattern).filter(
            AnalysisPattern.wallet_address.ilike(norm_wallet)
        )
        if case_id:
            pat_query = pat_query.filter(AnalysisPattern.case_id == case_id)
        patterns = pat_query.all()

        # 3. Fetch entity metadata
        label = db.query(AddressLabel).filter(
            AddressLabel.address.ilike(norm_wallet)
        ).first()
        entity_type = label.entity_type.value if label else "UNKNOWN"
        entity_name = label.entity_name if label else None

        # 4. Multi-hop graph to extract counterparties
        graph_res = GraphService.build_wallet_graph(
            db=db,
            wallet_address=norm_wallet,
            max_hops=max_hops,
            direction="both"
        )

        leads: List[PriorityItem] = []

        # (a) Target Wallet itself as primary lead
        tot_vol = sum(e.value_eth for e in graph_res.edges if e.from_address.lower() == norm_wallet or e.to_address.lower() == norm_wallet)
        root_calc = PriorityCalculationEngine.calculate_wallet_priority(
            wallet_address=norm_wallet,
            risk_score=risk_score,
            patterns=patterns,
            hops_from_source=0,
            total_volume_eth=tot_vol,
            entity_type=entity_type,
            entity_name=entity_name,
            is_source=True
        )

        root_lead = PriorityItem(
            object_type="WALLET",
            object_id=norm_wallet,
            wallet_address=norm_wallet,
            blockchain="Ethereum",
            chain_id=11155111,
            priority_score=root_calc["priority_score"],
            priority_category=root_calc["priority_category"],
            risk_score=risk_score,
            reasons=root_calc["reasons"],
            supporting_evidence=root_calc["supporting_evidence"] or [e.tx_hash for e in graph_res.edges[:3]],
            case_id=case_id,
            status="NEW",
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow()
        )
        leads.append(root_lead)

        # (b) Connected Counterparties / Transit Wallets
        for node in graph_res.nodes:
            node_addr = node.address.lower()
            if node_addr == norm_wallet:
                continue

            node_vol = node.total_incoming_value + node.total_outgoing_value
            node_risk = getattr(node, "risk_score", None)
            node_calc = PriorityCalculationEngine.calculate_wallet_priority(
                wallet_address=node_addr,
                risk_score=node_risk,
                patterns=[],
                hops_from_source=node.hops_from_root,
                total_volume_eth=node_vol,
                entity_type=node.entity_type,
                entity_name=node.entity_name
            )

            # Only add leads with meaningful priority (points >= 15 or known entity)
            if node_calc["priority_score"] >= 15.0 or node.entity_type != "UNKNOWN":
                node_lead = PriorityItem(
                    object_type="WALLET",
                    object_id=node_addr,
                    wallet_address=node_addr,
                    blockchain=node.blockchain or "Ethereum",
                    chain_id=11155111,
                    priority_score=node_calc["priority_score"],
                    priority_category=node_calc["priority_category"],
                    risk_score=node_risk,
                    reasons=node_calc["reasons"],
                    supporting_evidence=node_calc["supporting_evidence"] or [e.tx_hash for e in graph_res.edges if e.from_address.lower() == node_addr or e.to_address.lower() == node_addr][:2],
                    case_id=case_id,
                    status="NEW",
                    created_at=datetime.datetime.utcnow(),
                    updated_at=datetime.datetime.utcnow()
                )
                leads.append(node_lead)

        # Sort leads by priority_score descending
        leads.sort(key=lambda x: x.priority_score, reverse=True)

        persisted_leads = []
        if persist:
            for lead in leads:
                try:
                    # Check if already present to update
                    existing = db.query(PriorityItem).filter(
                        PriorityItem.object_id == lead.object_id,
                        PriorityItem.case_id == lead.case_id
                    ).first()
                    if existing:
                        existing.priority_score = lead.priority_score
                        existing.priority_category = lead.priority_category
                        existing.risk_score = lead.risk_score
                        existing.reasons = lead.reasons
                        existing.supporting_evidence = lead.supporting_evidence
                        existing.updated_at = datetime.datetime.utcnow()
                        db.commit()
                        db.refresh(existing)
                        persisted_leads.append(existing)
                    else:
                        db.add(lead)
                        db.commit()
                        db.refresh(lead)
                        persisted_leads.append(lead)
                except Exception:
                    db.rollback()
                    persisted_leads.append(lead)
            return persisted_leads

        return leads

    @staticmethod
    def prioritize_case(db: Session, case_id: str) -> List[PriorityItem]:
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if not case:
            raise ValueError(f"Case '{case_id}' not found.")

        return PriorityService.prioritize_wallet(
            db=db,
            wallet_address=case.suspect_wallet,
            case_id=case_id,
            max_hops=3,
            persist=True
        )

    @staticmethod
    def get_priority_queue(
        db: Session,
        case_id: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> PriorityQueueResponse:
        query = db.query(PriorityItem)
        if case_id:
            query = query.filter(PriorityItem.case_id == case_id)
        if category:
            query = query.filter(PriorityItem.priority_category == category.upper())
        if status:
            query = query.filter(PriorityItem.status == status.upper())

        all_items = query.order_by(desc(PriorityItem.priority_score)).all()
        if not all_items and not category and not status:
            try:
                PriorityService.prioritize_case(db=db, case_id=case_id or "CASE-SIH2026-001")
                all_items = query.order_by(desc(PriorityItem.priority_score)).all()
            except Exception:
                pass

        crit = sum(1 for i in all_items if i.priority_category == "CRITICAL")
        high = sum(1 for i in all_items if i.priority_category == "HIGH")
        med = sum(1 for i in all_items if i.priority_category == "MEDIUM")
        low = sum(1 for i in all_items if i.priority_category == "LOW")

        return PriorityQueueResponse(
            total_leads=len(all_items),
            critical_count=crit,
            high_count=high,
            medium_count=med,
            low_count=low,
            queue=[PriorityItemResponse.from_orm(i) for i in all_items[:limit]]
        )

    @staticmethod
    def get_priority_item(db: Session, priority_id: int) -> PriorityItem:
        item = db.query(PriorityItem).filter(PriorityItem.id == priority_id).first()
        if not item:
            raise ValueError(f"Priority item with ID {priority_id} not found.")
        return item

    @staticmethod
    def review_lead(
        db: Session,
        priority_id: int,
        status: str,
        notes: Optional[str] = None,
        username: Optional[str] = None
    ) -> PriorityItem:
        item = PriorityService.get_priority_item(db, priority_id)
        item.status = status.upper()
        if notes:
            item.notes = f"{item.notes or ''}\n[{username or 'Investigator'}]: {notes}".strip()
        item.updated_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def assign_lead(db: Session, priority_id: int, assigned_to: str) -> PriorityItem:
        item = PriorityService.get_priority_item(db, priority_id)
        item.assigned_to = assigned_to
        item.updated_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def add_lead_note(db: Session, priority_id: int, note_text: str, username: Optional[str] = None) -> PriorityItem:
        item = PriorityService.get_priority_item(db, priority_id)
        stamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        user_label = username or "Investigator"
        formatted_note = f"[{stamp}] {user_label}: {note_text}"
        if item.notes:
            item.notes = f"{item.notes}\n{formatted_note}"
        else:
            item.notes = formatted_note
        item.updated_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(item)
        return item
