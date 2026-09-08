import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from app.config import settings
from app.database.models import Wallet, Transaction, AddressLabel, RiskFinding, EntityType
from app.blockchain.ethereum import EthereumProvider
from app.blockchain.polygon import PolygonProvider
from app.blockchain.bnb import BNBProvider
from app.graph.graph_builder import GraphBuilder
from app.graph.path_analysis import PathAnalyzer
from app.risk.rules import SuspiciousPatternEngine
from app.risk.explainability import RiskExplainability
from app.risk.priority import InvestigationPriorityEngine
from app.risk.features import FeatureExtractor
from app.risk.model import MLRiskClassifier

class WalletService:
    ml_model = MLRiskClassifier()

    @staticmethod
    def get_provider(blockchain: str):
        b = blockchain.lower()
        if "polygon" in b:
            return PolygonProvider()
        elif "bnb" in b or "binance" in b:
            return BNBProvider()
        elif "mainnet" in b:
            return EthereumProvider(network="Mainnet")
        else:
            return EthereumProvider(network="Sepolia")

    @classmethod
    def analyze_wallet(
        cls,
        db: Session,
        address: str,
        blockchain: str = "Ethereum",
        hops: int = 2,
        case_id: Optional[str] = None
    ) -> Dict[str, Any]:
        provider = cls.get_provider(blockchain)
        is_valid = provider.validate_address(address)
        if not is_valid:
            raise ValueError(f"Invalid {blockchain} address format: {address}")

        norm_addr = address.strip().lower()

        # 1. Fetch cached transactions from DB (case-insensitive)
        db_txs = db.query(Transaction).filter(
            or_(
                func.lower(Transaction.from_address) == norm_addr,
                func.lower(Transaction.to_address) == norm_addr
            )
        ).all()

        # 2. If transactions in DB are low and not demo mode, attempt RPC / explorer retrieval
        if len(db_txs) < 2 and not settings.DEMO_MODE:
            try:
                live_txs = provider.get_transactions_for_wallet(norm_addr, limit=25)
                for ltx in live_txs:
                    existing_tx = db.query(Transaction).filter(
                        Transaction.transaction_hash == ltx.transaction_hash
                    ).first()
                    if not existing_tx:
                        new_tx = Transaction(
                            transaction_hash=ltx.transaction_hash,
                            blockchain=blockchain,
                            block_number=ltx.block_number,
                            timestamp=ltx.timestamp,
                            from_address=(ltx.from_address or "").lower(),
                            to_address=(ltx.to_address or "").lower(),
                            amount_native=ltx.amount_native,
                            amount_usd_if_available=ltx.amount_usd_if_available,
                            gas_used=ltx.gas_used,
                            gas_fee=ltx.gas_fee,
                            status=ltx.status,
                            case_id=case_id
                        )
                        db.add(new_tx)
                db.commit()
                # Re-query
                db_txs = db.query(Transaction).filter(
                    or_(
                        func.lower(Transaction.from_address) == norm_addr,
                        func.lower(Transaction.to_address) == norm_addr
                    )
                ).all()
            except Exception:
                pass

        # 3. Pull all relevant transactions for the case / connected hops
        all_case_txs = db.query(Transaction).all() if len(db_txs) < 10 else db_txs
        labels_map = {lbl.address.lower(): lbl for lbl in db.query(AddressLabel).all()}

        # 4. Construct Graph
        gb = GraphBuilder()
        gb.populate_from_transactions(all_case_txs, labels_map)
        graph = gb.get_graph()
        pa = PathAnalyzer(graph)

        # 5. Path Analysis & Subgraph
        subgraph = pa.get_k_hop_subgraph(norm_addr, max_hops=hops)
        vasp_paths = pa.trace_paths_to_vasp(norm_addr, max_hops=5)
        cycles = pa.find_cycles(norm_addr)

        # 6. Pattern Detection Rules
        findings = SuspiciousPatternEngine.evaluate_patterns(
            wallet_address=norm_addr,
            transactions=all_case_txs,
            labels_map=labels_map,
            max_hop_depth=hops,
            cycles_detected=cycles
        )

        # 7. Explainable Risk Score
        risk_data = RiskExplainability.compute_risk_score(findings)

        # 8. ML Inference
        features = FeatureExtractor.extract_wallet_features(norm_addr, all_case_txs, labels_map, hop_count=hops)
        ml_prediction = cls.ml_model.predict_risk(features)

        # 9. Priority Ranking
        ranked_wallets = InvestigationPriorityEngine.rank_wallets(subgraph["nodes"], labels_map, norm_addr)

        # 10. Update or create Wallet model
        w_record = db.query(Wallet).filter(
            func.lower(Wallet.address) == norm_addr,
            Wallet.blockchain == blockchain
        ).first()

        lbl_entry = labels_map.get(norm_addr)
        in_val = sum(t.amount_native for t in all_case_txs if (t.to_address or "").lower() == norm_addr)
        out_val = sum(t.amount_native for t in all_case_txs if (t.from_address or "").lower() == norm_addr)

        if not w_record:
            w_record = Wallet(
                address=norm_addr,
                blockchain=blockchain,
                label=lbl_entry.entity_name if lbl_entry else "Unknown Wallet",
                entity_type=lbl_entry.entity_type if lbl_entry else EntityType.UNKNOWN,
                risk_score=risk_data["score"],
                risk_level=risk_data["level"],
                total_incoming=in_val,
                total_outgoing=out_val,
                tx_count=len([t for t in all_case_txs if (t.from_address or "").lower() == norm_addr or (t.to_address or "").lower() == norm_addr])
            )
            db.add(w_record)
        else:
            w_record.risk_score = risk_data["score"]
            w_record.risk_level = risk_data["level"]
            w_record.total_incoming = in_val
            w_record.total_outgoing = out_val
            w_record.tx_count = len([t for t in all_case_txs if (t.from_address or "").lower() == norm_addr or (t.to_address or "").lower() == norm_addr])

        db.commit()

        return {
            "address": address,
            "blockchain": blockchain,
            "label": lbl_entry.entity_name if lbl_entry else "Unknown Wallet",
            "entity_type": lbl_entry.entity_type.value if lbl_entry else "UNKNOWN",
            "balance_native": provider.get_balance(address),
            "total_incoming": round(in_val, 4),
            "total_outgoing": round(out_val, 4),
            "risk_score": risk_data["score"],
            "risk_level": risk_data["level"],
            "reasons": risk_data["reasons"],
            "findings": findings,
            "subgraph": subgraph,
            "vasp_paths": vasp_paths,
            "priority_wallets": ranked_wallets[:10],
            "ml_assessment": ml_prediction,
            "disclaimer": risk_data["disclaimer"]
        }
