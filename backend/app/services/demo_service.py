import datetime
import json
from pathlib import Path
from sqlalchemy.orm import Session
from app.database.models import (
    Case, Wallet, Transaction, AddressLabel, RiskFinding,
    Evidence, CaseStatus, CasePriority, EntityType, ConfidenceLevel, FindingSeverity
)
from app.evidence.evidence_service import EvidenceService

class DemoService:
    # Deterministic demo wallet addresses
    VICTIM_WALLET = "0x95222290DD7278Aa3Ddd389Cc1E1d165CC4BAfe5"
    WALLET_A_SUSPECT = "0x4838B106FCe9647Bdf1E7877BF73cE8B0BAD5f97" # Wallet A
    WALLET_B_SPLITTER = "0x1Db3439a222C519ab44bb1144fC23cc742106cf2" # Wallet B
    WALLET_C = "0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD"
    WALLET_D = "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45"
    WALLET_F_MULE = "0x0d4a11d5EEaaC28EC3F61d100daF4d40471f1852"     # Wallet F
    WALLET_G_CONSOLIDATOR = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D" # Wallet G
    VASP_BINANCE_HOT = "0x28C6c06298d514Db089934071355E5743bf21d60"    # Binance 14

    @classmethod
    def seed_demo_case(cls, db: Session) -> Case:
        """
        Creates or resets the official SIH Hackathon Demo Case:
        Rahul lost ₹5,00,000 (2.5 ETH) across Wallet A -> B -> F -> G -> VASP (Binance).
        """
        case_id = "CASE-SIH2026-001"
        existing = db.query(Case).filter(Case.case_id == case_id).first()
        if existing:
            return existing

        now = datetime.datetime.utcnow()
        t0 = now - datetime.timedelta(hours=48)

        # 1. Ensure Address Labels are in DB
        labels_to_seed = [
            (cls.VASP_BINANCE_HOT, "Binance 14 (Hot Wallet)", EntityType.VASP, "Verified Exchange Hot Wallet"),
            (cls.WALLET_G_CONSOLIDATOR, "Suspect Layering Hub (Wallet G)", EntityType.UNKNOWN, "High-throughput transit address"),
            (cls.WALLET_F_MULE, "Money Mule Transit (Wallet F)", EntityType.UNKNOWN, "Short-lived transit wallet"),
            (cls.WALLET_B_SPLITTER, "Fund Splitting Hub (Wallet B)", EntityType.UNKNOWN, "Peeling chain distributor"),
            (cls.WALLET_A_SUSPECT, "Suspect Intake (Wallet A)", EntityType.UNKNOWN, "Direct recipient of victim deposit"),
            (cls.VICTIM_WALLET, "Rahul Sharma (Victim Wallet)", EntityType.UNKNOWN, "Victim funding source")
        ]

        for addr, name, etype, notes in labels_to_seed:
            lbl = db.query(AddressLabel).filter(AddressLabel.address == addr).first()
            if not lbl:
                db.add(AddressLabel(
                    address=addr,
                    blockchain="Ethereum",
                    entity_name=name,
                    entity_type=etype,
                    source="SIH Forensic Intel",
                    confidence=ConfidenceLevel.HIGH,
                    notes=notes
                ))

        # 2. Create Case Record
        case = Case(
            case_id=case_id,
            title="Rahul Sharma - ₹5 Lakh Phishing Theft to Binance VASP",
            victim_name="Rahul Sharma",
            complaint_reference="CR-2026-DEL-8942",
            amount_lost=500000.0,
            currency="INR",
            incident_date=t0,
            description=(
                "Victim was lured by an impersonation investment telegram group to transfer 2.5 ETH "
                "(approx ₹5,00,000) to suspect wallet A under pretext of high-yield arbitrage."
            ),
            suspect_wallet=cls.WALLET_A_SUSPECT,
            blockchain="Ethereum",
            transaction_hash="0xa1b2c3d4e5f6789012345678abcdef9012345678abcdef9012345678abcdef01",
            status=CaseStatus.UNDER_INVESTIGATION,
            priority=CasePriority.CRITICAL,
            created_at=t0
        )
        db.add(case)

        # 3. Create Demo Transactions (Chronological chain)
        tx_chain = [
            # Victim -> Wallet A (2.5 ETH)
            {
                "hash": "0xa1b2c3d4e5f6789012345678abcdef9012345678abcdef9012345678abcdef01",
                "from": cls.VICTIM_WALLET,
                "to": cls.WALLET_A_SUSPECT,
                "amt": 2.50,
                "ts": t0,
                "block": 19451000
            },
            # Wallet A -> Wallet B (2.48 ETH, 8 mins later - Rapid movement)
            {
                "hash": "0xb2c3d4e5f6789012345678abcdef9012345678abcdef9012345678abcdef02",
                "from": cls.WALLET_A_SUSPECT,
                "to": cls.WALLET_B_SPLITTER,
                "amt": 2.48,
                "ts": t0 + datetime.timedelta(minutes=8),
                "block": 19451040
            },
            # Wallet B -> Wallet F (1.20 ETH - Split 1)
            {
                "hash": "0xc3d4e5f6789012345678abcdef9012345678abcdef9012345678abcdef03",
                "from": cls.WALLET_B_SPLITTER,
                "to": cls.WALLET_F_MULE,
                "amt": 1.20,
                "ts": t0 + datetime.timedelta(minutes=14),
                "block": 19451070
            },
            # Wallet B -> Wallet C (0.80 ETH - Split 2)
            {
                "hash": "0xd4e5f6789012345678abcdef9012345678abcdef9012345678abcdef04",
                "from": cls.WALLET_B_SPLITTER,
                "to": cls.WALLET_C,
                "amt": 0.80,
                "ts": t0 + datetime.timedelta(minutes=15),
                "block": 19451075
            },
            # Wallet B -> Wallet D (0.48 ETH - Split 3)
            {
                "hash": "0xe5f6789012345678abcdef9012345678abcdef9012345678abcdef05",
                "from": cls.WALLET_B_SPLITTER,
                "to": cls.WALLET_D,
                "amt": 0.48,
                "ts": t0 + datetime.timedelta(minutes=17),
                "block": 19451085
            },
            # Wallet F -> Wallet G (1.18 ETH, 12 mins later)
            {
                "hash": "0xf6789012345678abcdef9012345678abcdef9012345678abcdef06",
                "from": cls.WALLET_F_MULE,
                "to": cls.WALLET_G_CONSOLIDATOR,
                "amt": 1.18,
                "ts": t0 + datetime.timedelta(minutes=29),
                "block": 19451145
            },
            # Wallet G -> Binance 14 VASP (1.15 ETH - Terminal Liquidation)
            {
                "hash": "0x012345678abcdef9012345678abcdef9012345678abcdef07",
                "from": cls.WALLET_G_CONSOLIDATOR,
                "to": cls.VASP_BINANCE_HOT,
                "amt": 1.15,
                "ts": t0 + datetime.timedelta(minutes=42),
                "block": 19451210
            }
        ]

        for item in tx_chain:
            tx = Transaction(
                transaction_hash=item["hash"],
                blockchain="Ethereum",
                block_number=item["block"],
                timestamp=item["ts"],
                from_address=item["from"],
                to_address=item["to"],
                amount_native=item["amt"],
                amount_usd_if_available=round(item["amt"] * 3000.0, 2),
                gas_used=21000.0,
                gas_fee=0.00042,
                status="SUCCESS",
                case_id=case_id
            )
            db.add(tx)

        # 4. Create Pre-detected Risk Findings
        findings_data = [
            (
                "RAPID_MOVEMENT",
                FindingSeverity.HIGH,
                15.0,
                [tx_chain[1]["hash"]],
                "Funds (2.48 ETH) moved from Wallet A to Wallet B within 8 minutes of deposit."
            ),
            (
                "FUND_SPLITTING",
                FindingSeverity.HIGH,
                15.0,
                [tx_chain[2]["hash"], tx_chain[3]["hash"], tx_chain[4]["hash"]],
                "Peeling chain structuring: Wallet B split 2.48 ETH into 3 distinct downstream addresses."
            ),
            (
                "MULTI_HOP_DEPTH",
                FindingSeverity.HIGH,
                15.0,
                [item["hash"] for item in tx_chain[:4]],
                "Layering trail spans 4 distinct hops from victim source to liquidation destination."
            ),
            (
                "VASP_LIQUIDATION_EXIT",
                FindingSeverity.CRITICAL,
                20.0,
                [tx_chain[-1]["hash"]],
                "Stolen funds exited through verified centralized exchange Binance 14 (Hot Wallet)."
            ),
            (
                "UNUSUAL_TRANSACTION_BURST",
                FindingSeverity.MEDIUM,
                10.0,
                [item["hash"] for item in tx_chain],
                "Entire 4-hop liquidation sequence executed in under 45 minutes."
            ),
            (
                "SUDDEN_LARGE_TRANSFER",
                FindingSeverity.HIGH,
                16.0,
                [tx_chain[0]["hash"]],
                "Initial theft deposit of 2.50 ETH exceeds threshold for high-priority monitoring."
            )
        ]

        for ftype, sev, delta, ev_txs, expl in findings_data:
            finding = RiskFinding(
                case_id=case_id,
                wallet_address=cls.WALLET_A_SUSPECT,
                finding_type=ftype,
                severity=sev,
                score_delta=delta,
                evidence_txs=ev_txs,
                explanation=expl
            )
            db.add(finding)

        # 5. Create Initial Evidence Locker Entry
        ev_hash = EvidenceService.compute_integrity_hash(
            case_id=case_id,
            tx_hash=tx_chain[-1]["hash"],
            from_address=cls.WALLET_G_CONSOLIDATOR,
            to_address=cls.VASP_BINANCE_HOT,
            amount=1.15,
            timestamp_str=tx_chain[-1]["ts"].isoformat()
        )
        evidence = Evidence(
            evidence_id="EV-SIH2026-DEMO",
            case_id=case_id,
            blockchain="Ethereum",
            wallet=cls.WALLET_G_CONSOLIDATOR,
            transaction_hash=tx_chain[-1]["hash"],
            block_number=tx_chain[-1]["block"],
            timestamp=tx_chain[-1]["ts"],
            from_address=cls.WALLET_G_CONSOLIDATOR,
            to_address=cls.VASP_BINANCE_HOT,
            amount=1.15,
            finding_type="VASP_LIQUIDATION_EXIT",
            tag="PRIMARY_FLOW",
            source="Sepolia/Mainnet Ledger",
            investigator_notes="Terminal liquidation hop into Binance Hot Wallet. Prepared for emergency VASP freeze notice.",
            importance="CRITICAL",
            integrity_hash=ev_hash
        )
        db.add(evidence)

        db.commit()
        db.refresh(case)
        return case
