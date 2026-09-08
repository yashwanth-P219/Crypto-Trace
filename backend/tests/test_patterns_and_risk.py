import datetime
import pytest
from app.database.models import Transaction, AddressLabel, EntityType, ConfidenceLevel
from app.risk.rules import SuspiciousPatternEngine
from app.risk.explainability import RiskExplainability
from app.risk.priority import InvestigationPriorityEngine

def test_rapid_movement_rule():
    t0 = datetime.datetime.utcnow()
    # Deposit 2.0 ETH at t0, send out 1.9 ETH 4 minutes later
    tx_in = Transaction(
        transaction_hash="0xin01",
        blockchain="Ethereum",
        block_number=1,
        timestamp=t0,
        from_address="0xSender",
        to_address="0xSuspect",
        amount_native=2.0
    )
    tx_out = Transaction(
        transaction_hash="0xout01",
        blockchain="Ethereum",
        block_number=2,
        timestamp=t0 + datetime.timedelta(minutes=4),
        from_address="0xSuspect",
        to_address="0xReceiver",
        amount_native=1.9
    )

    findings = SuspiciousPatternEngine.evaluate_patterns(
        wallet_address="0xSuspect",
        transactions=[tx_in, tx_out],
        labels_map={}
    )
    types = [f["finding_type"] for f in findings]
    assert "RAPID_MOVEMENT" in types

def test_fund_splitting_rule():
    t0 = datetime.datetime.utcnow()
    tx_in = Transaction(
        transaction_hash="0xin01",
        blockchain="Ethereum",
        timestamp=t0,
        from_address="0xSender",
        to_address="0xSuspect",
        amount_native=5.0
    )
    outgoings = [
        Transaction(
            transaction_hash=f"0xout0{i}",
            blockchain="Ethereum",
            timestamp=t0 + datetime.timedelta(minutes=i*2),
            from_address="0xSuspect",
            to_address=f"0xSplit{i}",
            amount_native=1.0
        )
        for i in range(1, 4)
    ]

    findings = SuspiciousPatternEngine.evaluate_patterns(
        wallet_address="0xSuspect",
        transactions=[tx_in] + outgoings,
        labels_map={}
    )
    types = [f["finding_type"] for f in findings]
    assert "FUND_SPLITTING" in types

def test_risk_explainability_scoring():
    findings = [
        {"finding_type": "RAPID_MOVEMENT", "score_delta": 15.0, "explanation": "Rapid exit", "evidence_txs": ["0x1"]},
        {"finding_type": "FUND_SPLITTING", "score_delta": 15.0, "explanation": "Split exit", "evidence_txs": ["0x2"]},
        {"finding_type": "MULTI_HOP_DEPTH", "score_delta": 15.0, "explanation": "3 hops", "evidence_txs": ["0x3"]},
        {"finding_type": "HIGH_RISK_COUNTERPARTY", "score_delta": 20.0, "explanation": "Mixer hit", "evidence_txs": ["0x4"]}
    ]
    summary = RiskExplainability.compute_risk_score(findings)
    assert summary["score"] == 65.0
    assert summary["level"] == "HIGH"
    assert len(summary["reasons"]) == 4

def test_investigation_priority_engine():
    nodes = [
        {
            "address": "0xNormalUser",
            "entity_type": "UNKNOWN",
            "total_incoming": 0.1,
            "total_outgoing": 0.0,
            "hops_from_source": 3,
            "risk_score": 10.0
        },
        {
            "address": "0xVASPExit",
            "entity_type": "VASP",
            "label": "Binance 14",
            "total_incoming": 2.5,
            "total_outgoing": 0.0,
            "hops_from_source": 2,
            "risk_score": 85.0
        }
    ]
    labels_map = {
        "0xvaspexit": AddressLabel(
            address="0xVASPExit",
            blockchain="Ethereum",
            entity_name="Binance 14",
            entity_type=EntityType.VASP,
            source="Intel",
            confidence=ConfidenceLevel.HIGH
        )
    }

    ranked = InvestigationPriorityEngine.rank_wallets(nodes, labels_map, source_address="0xSource")
    assert len(ranked) == 2
    assert ranked[0]["address"] == "0xVASPExit"
    assert ranked[0]["priority_level"] in ("CRITICAL", "HIGH")
    assert ranked[0]["priority_rank"] == 1
