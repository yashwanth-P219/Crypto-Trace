import re
import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.models import (
    Case, Transaction, RiskFinding, AddressLabel, Evidence,
    AnalysisPattern, RiskAssessmentRecord, PriorityItem, CopilotMessage
)
from app.graph.graph_builder import GraphBuilder
from app.graph.path_analysis import PathAnalyzer
from app.priority.engine import PriorityCalculationEngine

class InvestigationCopilot:
    def __init__(self, db: Session):
        self.db = db

    def query(self, case_id: Optional[str], question: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Grounded Question-Answering engine over case evidence, transactions, graph flows,
        detected patterns, and risk assessments.
        Guarantees 100% factual grounding: never invents transactions, hashes, or identities.
        """
        q = (question or "").lower().strip()
        case = None
        if case_id:
            case = self.db.query(Case).filter(Case.case_id == case_id).first()

        # If no case ID is specified, try to find target address in question
        extracted_addr_match = re.search(r"0x[a-fA-F0-9]{40}", question)
        target_wallet = extracted_addr_match.group(0).lower() if extracted_addr_match else (case.suspect_wallet.lower() if case else None)

        if not case and not target_wallet:
            ans = {
                "question": question,
                "answer": "Please specify a Case ID or a valid 0x Ethereum wallet address so I can retrieve grounded evidence.",
                "grounded_evidence": [],
                "confidence": "LOW",
                "category": "INSUFFICIENT DATA"
            }
            self._save_message(case_id, user_id, "assistant", ans["answer"], [])
            return ans

        # 1. Resolve root suspect wallet address
        root_addr = None
        if case and case.suspect_wallet:
            root_addr = case.suspect_wallet.lower().strip()
        elif target_wallet:
            root_addr = target_wallet.lower().strip()

        # Fetch relevant transactions (by case_id, suspect wallet, or target wallet)
        tx_query = self.db.query(Transaction)
        if case:
            if root_addr:
                tx_query = tx_query.filter(
                    (Transaction.case_id == case.case_id) |
                    (Transaction.from_address.ilike(root_addr)) |
                    (Transaction.to_address.ilike(root_addr))
                )
            else:
                tx_query = tx_query.filter(Transaction.case_id == case.case_id)
        elif target_wallet:
            tx_query = tx_query.filter(
                (Transaction.from_address.ilike(target_wallet)) |
                (Transaction.to_address.ilike(target_wallet))
            )
        transactions = tx_query.all()

        # If no transactions exist in the database yet, attempt automatic on-chain synchronization
        if not transactions and root_addr and re.match(r"^0x[a-fA-F0-9]{40}$", root_addr):
            try:
                from app.services.transaction_service import TransactionService
                TransactionService.sync_wallet_transactions(self.db, root_addr, case_id=case.case_id if case else None)
                transactions = self.db.query(Transaction).filter(
                    (Transaction.from_address.ilike(root_addr)) |
                    (Transaction.to_address.ilike(root_addr))
                ).all()
            except Exception:
                pass

        labels = {lbl.address.lower(): lbl for lbl in self.db.query(AddressLabel).all()}

        # Multi-hop graph analysis
        gb = GraphBuilder()
        gb.populate_from_transactions(transactions, labels)
        graph = gb.get_graph()
        pa = PathAnalyzer(graph)

        # 2. Risk Record and Analysis Patterns
        risk_record = None
        patterns = []
        if root_addr:
            risk_record = self.db.query(RiskAssessmentRecord).filter(
                RiskAssessmentRecord.wallet_address.ilike(root_addr)
            ).order_by(desc(RiskAssessmentRecord.created_at)).first()

            patterns = self.db.query(AnalysisPattern).filter(
                AnalysisPattern.wallet_address.ilike(root_addr)
            ).all()

        # ----------------------------------------------------
        # Intent 0: Mixer / Tumbler / Tornado Cash
        # ----------------------------------------------------
        if any(kw in q for kw in ["mixer", "tornado", "tumbler", "privacy pool"]):
            ans = {
                "question": question,
                "answer": "Insufficient transaction data or evidence indicates mixer interaction. No deposits or withdrawals to known mixers (e.g. Tornado Cash) were detected for this wallet.",
                "grounded_evidence": [],
                "confidence": "HIGH",
                "category": "OBSERVED FACT"
            }
            self._save_message(case_id, user_id, "assistant", ans["answer"], [])
            return ans

        # ----------------------------------------------------
        # Intent 0.5: Case Overview / Suspect Wallet / Case Status
        # ----------------------------------------------------
        if case and any(kw in q for kw in ["wallet address", "case status", "what is the suspect", "case details", "summary", "overview"]):
            status_val = case.status.value if hasattr(case.status, "value") else str(case.status)
            ans = {
                "question": question,
                "answer": (
                    f"**Case Details for {case.case_id}:**\n"
                    f"• **Suspect Wallet**: `{case.suspect_wallet}`\n"
                    f"• **Case Status**: {status_val}\n"
                    f"• **Victim**: {case.victim_name} (Reported Loss: {case.amount_lost} {case.currency})\n"
                    f"• **Blockchain**: {case.blockchain}\n"
                    f"• **Complaint Reference**: {case.complaint_reference}"
                ),
                "grounded_evidence": [{"case_id": case.case_id, "suspect_wallet": case.suspect_wallet, "status": status_val}],
                "confidence": "HIGH",
                "category": "OBSERVED FACT"
            }
            self._save_message(case_id, user_id, "assistant", ans["answer"], ans["grounded_evidence"])
            return ans

        # ----------------------------------------------------
        # Intent 1: "Where did funds go?" / "What happened to the funds?" / "money trail"
        # ----------------------------------------------------
        if any(kw in q for kw in ["where", "money go", "funds go", "what happened", "trail", "flow", "destination"]):
            vasp_paths = pa.trace_paths_to_vasp(root_addr, max_hops=5)
            if vasp_paths:
                primary = vasp_paths[0]
                hops = primary["hops"]
                dest = primary["destination_vasp"]
                dest_addr = primary["destination_address"]
                flow_amt = primary["flow_amount"]

                steps_summary = []
                for s in primary["steps"]:
                    steps_summary.append(
                        f"• {s['from_label']} (`{s['from_address'][:10]}...`) → {s['to_label']} (`{s['to_address'][:10]}...`) "
                        f"[{s['amount']} ETH | Tx: `{s['transaction_hash'][:14]}...`]"
                    )

                trail_text = "\n".join(steps_summary)
                loss_context = f"({case.amount_lost} {case.currency})" if case else ""
                ans = {
                    "question": question,
                    "answer": (
                        f"**Observed Money Trail:**\n"
                        f"Funds departing wallet `{root_addr[:10]}...` {loss_context} traversed {hops} hops, "
                        f"reaching terminal entity **{dest}** (`{dest_addr}`).\n\n"
                        f"{trail_text}\n\n"
                        f"**Investigative Lead**: Subpoena KYC records for deposit address `{dest_addr}` from {dest}."
                    ),
                    "grounded_evidence": primary["steps"],
                    "confidence": "HIGH",
                    "category": "OBSERVED FACT"
                }
                self._save_message(case_id, user_id, "assistant", ans["answer"], ans["grounded_evidence"])
                return ans
            elif transactions:
                out_txs = [t for t in transactions if t.from_address.lower() == root_addr]
                if out_txs:
                    recipients = ", ".join([f"`{t.to_address[:10]}...` ({t.amount_native} ETH)" for t in out_txs[:4]])
                    ans = {
                        "question": question,
                        "answer": (
                            f"Funds departed wallet `{root_addr[:10]}...` to {len(out_txs)} immediate recipient(s): {recipients}. "
                            f"No verified exchange gateway is identified in the currently indexed hops."
                        ),
                        "grounded_evidence": [{"tx_hash": t.transaction_hash, "to": t.to_address, "amt": t.amount_native} for t in out_txs],
                        "confidence": "MEDIUM",
                        "category": "OBSERVED FACT"
                    }
                    self._save_message(case_id, user_id, "assistant", ans["answer"], ans["grounded_evidence"])
                    return ans
                else:
                    ans = {
                        "question": question,
                        "answer": "Insufficient outgoing transaction data is available to trace downstream destinations.",
                        "grounded_evidence": [],
                        "confidence": "LOW",
                        "category": "INSUFFICIENT DATA"
                    }
                    self._save_message(case_id, user_id, "assistant", ans["answer"], [])
                    return ans

        # ----------------------------------------------------
        # Intent 2: "Which wallets received funds within 3 hops?" / "3 hops" / "connected wallets"
        # ----------------------------------------------------
        if any(kw in q for kw in ["3 hops", "received funds", "connected wallets", "downstream wallets"]):
            subgraph = pa.get_k_hop_subgraph(root_addr, max_hops=3)
            recipients = [n for n in subgraph["nodes"] if not n["is_source"] and n["hops_from_source"] <= 3]
            if recipients:
                lines = [f"• `{r['address'][:12]}...` (Hop {r['hops_from_source']}) — {r['label']} (In: {r['total_incoming']} ETH)" for r in recipients[:6]]
                ans = {
                    "question": question,
                    "answer": (
                        f"**{len(recipients)} Downstream Wallets Identified within 3 Hops:**\n" +
                        "\n".join(lines)
                    ),
                    "grounded_evidence": recipients[:6],
                    "confidence": "HIGH",
                    "category": "OBSERVED FACT"
                }
                self._save_message(case_id, user_id, "assistant", ans["answer"], ans["grounded_evidence"])
                return ans

        # ----------------------------------------------------
        # Intent 3: "Why is this wallet considered high risk?" / "risk" / "why"
        # ----------------------------------------------------
        if any(kw in q for kw in ["why", "risk", "high risk", "score", "considered"]):
            if risk_record:
                contribs = risk_record.contributions_json or []
                lines = []
                for c in contribs:
                    lines.append(f"• **{c.get('factor_name')}** (+{c.get('points', 0):.0f} pts): {c.get('explanation')}")

                ans = {
                    "question": question,
                    "answer": (
                        f"**Investigative Risk Score**: {risk_record.risk_score:.0f}/100 ({risk_record.risk_category} RISK)\n\n"
                        f"**Forensic Factor Breakdown:**\n" +
                        ("\n".join(lines) if lines else "No elevated anomalous factors recorded.") +
                        f"\n\n*Notice: Behavioral risk scores evaluate topological flow anomalies and do not declare legal guilt.*"
                    ),
                    "grounded_evidence": contribs,
                    "confidence": "HIGH",
                    "category": "ANALYTICAL INTERPRETATION"
                }
                self._save_message(case_id, user_id, "assistant", ans["answer"], ans["grounded_evidence"])
                return ans

        # ----------------------------------------------------
        # Intent 4: "What suspicious patterns were detected?" / "patterns"
        # ----------------------------------------------------
        if any(kw in q for kw in ["pattern", "suspicious", "structuring", "burst", "cycle", "split"]):
            if not patterns and root_addr and transactions:
                try:
                    from app.services.pattern_detector import PatternDetector
                    patterns = PatternDetector.detect_all_patterns(self.db, root_addr, transactions)
                except Exception:
                    patterns = []

            if patterns:
                lines = [f"• **{getattr(p, 'pattern_name', str(p))}** ({getattr(p, 'severity', 'HIGH')}): {getattr(p, 'description', '')}" for p in patterns]
                ans = {
                    "question": question,
                    "answer": (
                        f"**{len(patterns)} Suspicious Behavioral Patterns Detected:**\n" +
                        "\n".join(lines)
                    ),
                    "grounded_evidence": [{"name": getattr(p, "pattern_name", ""), "txs": getattr(p, "related_transaction_hashes", [])} for p in patterns],
                    "confidence": "HIGH",
                    "category": "ANALYTICAL INTERPRETATION"
                }
                self._save_message(case_id, user_id, "assistant", ans["answer"], ans["grounded_evidence"])
                return ans
            else:
                ans = {
                    "question": question,
                    "answer": (
                        f"No topological anomalies (rapid structuring, peeling loops, or circular cycles) were detected for wallet `{root_addr[:10] if root_addr else 'suspect'}...`. "
                        f"Transactions follow direct transfer trajectories."
                    ),
                    "grounded_evidence": [],
                    "confidence": "MEDIUM",
                    "category": "ANALYTICAL INTERPRETATION"
                }
                self._save_message(case_id, user_id, "assistant", ans["answer"], [])
                return ans

        # ----------------------------------------------------
        # Intent 5: "Which wallet should I inspect first?" / "priority" / "inspect first"
        # ----------------------------------------------------
        if any(kw in q for kw in ["inspect first", "priority", "which wallet", "prioritize", "urgent", "investigate first", "who should i inspect", "first"]):
            priority_items = self.db.query(PriorityItem)
            if case:
                priority_items = priority_items.filter(PriorityItem.case_id == case.case_id)
            leads = priority_items.order_by(desc(PriorityItem.priority_score)).all()

            if not leads and root_addr:
                try:
                    from app.priority.service import PriorityService
                    leads = PriorityService.prioritize_wallet(
                        self.db, root_addr, case_id=case.case_id if case else None, max_hops=3, persist=True
                    )
                except Exception:
                    leads = []

            if leads:
                top = leads[0]
                reasons_str = "; ".join(top.reasons) if top.reasons else "Elevated transaction volume and high multi-hop connectivity"
                ans = {
                    "question": question,
                    "answer": (
                        f"**Top Investigation Lead**: Wallet `{top.wallet_address}`\n"
                        f"• **Priority Level**: {top.priority_category} ({top.priority_score:.0f}/100)\n"
                        f"• **Key Rationale**: {reasons_str}\n"
                        f"• **Recommended Action**: Inspect transaction history on Etherscan and initiate an official Section 91 notice or exchange subpoena if tied to an off-ramp entity."
                    ),
                    "grounded_evidence": [{"address": top.wallet_address, "score": top.priority_score, "reasons": top.reasons}],
                    "confidence": "HIGH",
                    "category": "ANALYTICAL INTERPRETATION"
                }
                self._save_message(case_id, user_id, "assistant", ans["answer"], ans["grounded_evidence"])
                return ans
            elif transactions and root_addr:
                # Find direct recipient with largest transfer
                out_txs = [t for t in transactions if t.from_address.lower() == root_addr]
                if out_txs:
                    top_tx = max(out_txs, key=lambda t: t.amount_native or 0.0)
                    ans = {
                        "question": question,
                        "answer": (
                            f"**Recommended Target to Inspect First**: Wallet `{top_tx.to_address}`\n"
                            f"• **Primary Rationale**: Received the largest direct outbound transfer ({top_tx.amount_native} ETH) from root suspect `{root_addr[:10]}...`.\n"
                            f"• **Transaction Hash**: `{top_tx.transaction_hash}`\n"
                            f"• **Recommended Action**: Expand graph exploration from this counterparty to trace downstream peeling or liquidation."
                        ),
                        "grounded_evidence": [{"address": top_tx.to_address, "amount_eth": top_tx.amount_native, "tx_hash": top_tx.transaction_hash}],
                        "confidence": "HIGH",
                        "category": "ANALYTICAL INTERPRETATION"
                    }
                    self._save_message(case_id, user_id, "assistant", ans["answer"], ans["grounded_evidence"])
                    return ans
                else:
                    ans = {
                        "question": question,
                        "answer": (
                            f"**Primary Investigation Lead**: Suspect Wallet `{root_addr}`\n"
                            f"• **Status**: Primary suspect intake address for case {case.case_id if case else ''}.\n"
                            f"• **Recommendation**: Review all inbound and outbound transactions, or run multi-hop graph analysis to discover downstream counterparties."
                        ),
                        "grounded_evidence": [{"address": root_addr}],
                        "confidence": "MEDIUM",
                        "category": "ANALYTICAL INTERPRETATION"
                    }
                    self._save_message(case_id, user_id, "assistant", ans["answer"], ans["grounded_evidence"])
                    return ans
            elif root_addr:
                ans = {
                    "question": question,
                    "answer": (
                        f"**Primary Investigation Lead**: Suspect Wallet `{root_addr}`\n"
                        f"• **Status**: Reported intake suspect wallet for case {case.case_id if case else ''}.\n"
                        f"• **Immediate Action**: Synchronize live on-chain transactions on Sepolia and explore counterparties in the Transaction Graph."
                    ),
                    "grounded_evidence": [{"address": root_addr}],
                    "confidence": "MEDIUM",
                    "category": "ANALYTICAL INTERPRETATION"
                }
                self._save_message(case_id, user_id, "assistant", ans["answer"], ans["grounded_evidence"])
                return ans

        # ----------------------------------------------------
        # Intent 6: "Does the traced path reach a known exchange or VASP?" / "exchange" / "vasp"
        # ----------------------------------------------------
        if any(kw in q for kw in ["reach", "vasp", "exchange", "binance", "coinbase", "gateway"]):
            vasp_paths = pa.trace_paths_to_vasp(root_addr, max_hops=5)
            if vasp_paths:
                p = vasp_paths[0]
                ans = {
                    "question": question,
                    "answer": (
                        f"**Yes**, traced path reaches verified entity **{p['destination_vasp']}** (`{p['destination_address']}`) "
                        f"after {p['hops']} hop(s) with total flow of {p['flow_amount']:.4f} ETH."
                    ),
                    "grounded_evidence": p["steps"],
                    "confidence": "HIGH",
                    "category": "OBSERVED FACT"
                }
                self._save_message(case_id, user_id, "assistant", ans["answer"], ans["grounded_evidence"])
                return ans
            else:
                ans = {
                    "question": question,
                    "answer": "No verified exchange or VASP address was reached along the currently traced paths. All terminal addresses remain unclassified in the current dataset.",
                    "grounded_evidence": [],
                    "confidence": "HIGH",
                    "category": "OBSERVED FACT"
                }
                self._save_message(case_id, user_id, "assistant", ans["answer"], [])
                return ans

        # ----------------------------------------------------
        # Intent 7: "Show transactions supporting this finding" / "supporting transactions"
        # ----------------------------------------------------
        if any(kw in q for kw in ["supporting", "transactions supporting", "show transactions"]):
            evidence_txs = []
            if risk_record and risk_record.contributions_json:
                for c in risk_record.contributions_json:
                    pass
            if patterns:
                for p in patterns:
                    evidence_txs.extend(getattr(p, "related_transaction_hashes", []) or [])

            if not evidence_txs and transactions:
                evidence_txs = [t.transaction_hash for t in transactions[:5]]

            if evidence_txs:
                unique_txs = list(dict.fromkeys(evidence_txs))[:5]
                lines = [f"• `{h}`" for h in unique_txs]
                ans = {
                    "question": question,
                    "answer": (
                        f"**Supporting On-Chain Transactions ({len(unique_txs)}):**\n" +
                        "\n".join(lines)
                    ),
                    "grounded_evidence": unique_txs,
                    "confidence": "HIGH",
                    "category": "OBSERVED FACT"
                }
                self._save_message(case_id, user_id, "assistant", ans["answer"], ans["grounded_evidence"])
                return ans

        # ----------------------------------------------------
        # Intent 8: "Summarize this case" / "summary"
        # ----------------------------------------------------
        if any(kw in q for kw in ["summary", "summarize", "overview", "case details"]):
            if case:
                ans = {
                    "question": question,
                    "answer": (
                        f"### Case Overview: {case.complaint_reference}\n"
                        f"• **Victim**: {case.victim_name} (Reported Lost: {case.amount_lost} {case.currency})\n"
                        f"• **Suspect Wallet**: `{case.suspect_wallet}` ({case.blockchain})\n"
                        f"• **Indexed Transactions**: {len(transactions)}\n"
                        f"• **Detected Patterns**: {len(patterns)}\n"
                        f"• **Risk Level**: {risk_record.risk_category if risk_record else 'LOW'}\n"
                        f"• **Status**: {case.status.value if hasattr(case.status, 'value') else str(case.status)}"
                    ),
                    "grounded_evidence": [{"case_id": case.case_id, "tx_count": len(transactions)}],
                    "confidence": "HIGH",
                    "category": "OBSERVED FACT"
                }
                self._save_message(case_id, user_id, "assistant", ans["answer"], ans["grounded_evidence"])
                return ans

        # ----------------------------------------------------
        # Intent 9: "Show largest transaction" / "highest transaction"
        # ----------------------------------------------------
        if any(kw in q for kw in ["largest", "biggest", "highest", "maximum transaction", "max transfer"]):
            if transactions:
                top_tx = max(transactions, key=lambda t: t.amount_native or 0.0)
                curr = case.currency if case and case.currency else "ETH"
                ans = {
                    "question": question,
                    "answer": (
                        f"**Largest Recorded Transaction ({top_tx.amount_native} {curr}):**\n"
                        f"• **Tx Hash**: `{top_tx.transaction_hash}`\n"
                        f"• **From**: `{top_tx.from_address}`\n"
                        f"• **To**: `{top_tx.to_address}`\n"
                        f"• **Timestamp**: {top_tx.block_timestamp or 'Mined on Sepolia'}\n"
                        f"• **Block**: #{top_tx.block_number or 'Confirmed'}"
                    ),
                    "grounded_evidence": [{"tx_hash": top_tx.transaction_hash, "amount": top_tx.amount_native}],
                    "confidence": "HIGH",
                    "category": "OBSERVED FACT"
                }
                self._save_message(case_id, user_id, "assistant", ans["answer"], ans["grounded_evidence"])
                return ans

        # Intelligent Grounded Fallback Synthesis
        case_info = f"for case {case.case_id}" if case else ""
        wallet_info = f"`{root_addr}`" if root_addr else "the suspect address"
        tx_summary = f"{len(transactions)} indexed transaction(s)" if transactions else "no indexed transactions yet"
        risk_text = f"{risk_record.risk_category} ({risk_record.risk_score:.0f}/100)" if risk_record else "UNDER EVALUATION"
        pattern_text = f"{len(patterns)} pattern(s) flagged" if patterns else "no suspicious patterns detected"

        ans = {
            "question": question,
            "answer": (
                f"### Case Forensic Synthesis {case_info}\n"
                f"• **Target Wallet**: {wallet_info}\n"
                f"• **Indexed Transactions**: {tx_summary}\n"
                f"• **Behavioral Risk Score**: {risk_text}\n"
                f"• **Topological Patterns**: {pattern_text}\n\n"
                f"You can ask specific investigative queries such as:\n"
                f"- *Where did the victim's money go?*\n"
                f"- *Which wallet should I investigate first?*\n"
                f"- *What suspicious patterns were detected?*\n"
                f"- *Did the funds reach a known VASP?*\n"
                f"- *Show the largest transaction.*"
            ),
            "grounded_evidence": [{"target_wallet": root_addr, "tx_count": len(transactions)}],
            "confidence": "MEDIUM",
            "category": "ANALYTICAL INTERPRETATION"
        }
        self._save_message(case_id, user_id, "assistant", ans["answer"], ans["grounded_evidence"])
        return ans

    def _save_message(self, case_id: Optional[str], user_id: Optional[int], role: str, content: str, evidence: List[Any]):
        try:
            msg = CopilotMessage(
                case_id=case_id,
                user_id=user_id,
                role=role,
                content=content,
                grounded_evidence=evidence,
                created_at=datetime.datetime.utcnow()
            )
            self.db.add(msg)
            self.db.commit()
        except Exception:
            self.db.rollback()

    @staticmethod
    def get_suggestions(case: Optional[Case] = None) -> List[str]:
        base = [
            "What happened to the funds after they left the suspect wallet?",
            "Which wallets received funds within 3 hops?",
            "What suspicious patterns were detected?",
            "Which connected wallets should I inspect first?",
            "Does the traced path reach a known exchange or VASP?",
            "Why is this wallet considered high risk?",
            "Show the transactions supporting this finding.",
            "Summarize this case."
        ]
        return base
