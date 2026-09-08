import uuid
import datetime
import io
import json
import csv
import hashlib
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.database.models import (
    Case, Transaction, RiskFinding, Evidence, AddressLabel,
    InvestigatorNote, AuditLog, Report, ReportStatus, User
)
from app.graph.graph_builder import GraphBuilder
from app.graph.path_analysis import PathAnalyzer
from app.risk.explainability import RiskExplainability
from app.risk.priority import InvestigationPriorityEngine
from app.risk.risk_service import RiskService

class ReportGenerator:
    @staticmethod
    def generate_case_report(
        db: Session,
        case_id: str,
        investigator_user: User,
        custom_title: Optional[str] = None
    ) -> Report:
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if not case:
            raise ValueError(f"Case {case_id} not found")

        norm_suspect = (case.suspect_wallet or "").strip().lower()

        # Query direct transactions involving suspect wallet or case (case-insensitive)
        transactions = db.query(Transaction).filter(
            (Transaction.case_id == case_id) |
            (Transaction.from_address.ilike(norm_suspect)) |
            (Transaction.to_address.ilike(norm_suspect))
        ).all()

        # Multi-hop counterparty expansion to trace through hops to VASPs
        counterparties = {t.from_address.lower() for t in transactions if t.from_address} | {t.to_address.lower() for t in transactions if t.to_address}
        if counterparties:
            more_txs = db.query(Transaction).filter(
                (Transaction.from_address.in_(counterparties)) |
                (Transaction.to_address.in_(counterparties))
            ).all()
            tx_map = {t.transaction_hash: t for t in transactions + more_txs}
            transactions = list(tx_map.values())

        labels = {lbl.address.lower(): lbl for lbl in db.query(AddressLabel).all()}
        findings = db.query(RiskFinding).filter(RiskFinding.case_id == case_id).all()
        evidence_items = db.query(Evidence).filter(Evidence.case_id == case_id).all()
        notes = db.query(InvestigatorNote).filter(InvestigatorNote.case_id == case_id).all()
        audit_records = db.query(AuditLog).filter(AuditLog.case_id == case_id).order_by(AuditLog.timestamp.asc()).all()

        # Build Graph and Path Analysis
        gb = GraphBuilder()
        gb.populate_from_transactions(transactions, labels)
        graph = gb.get_graph()
        pa = PathAnalyzer(graph)

        subgraph_meta = pa.get_k_hop_subgraph(norm_suspect, max_hops=4)
        vasp_paths = pa.trace_paths_to_vasp(norm_suspect, max_hops=5)
        ranked_wallets = InvestigationPriorityEngine.rank_wallets(subgraph_meta["nodes"], labels, norm_suspect)

        # AI Risk Assessment & Dynamic Behavioral Patterns
        case_risk = None
        try:
            case_risk = RiskService.assess_case_risk(db=db, case_id=case_id, max_hops=4)
        except Exception:
            case_risk = None

        patterns_inferred = []
        if findings:
            for f in findings:
                patterns_inferred.append({
                    "type": f.finding_type,
                    "severity": f.severity.value if hasattr(f.severity, "value") else str(f.severity),
                    "explanation": f.explanation,
                    "evidence_txs": f.evidence_txs
                })

        if case_risk and case_risk.contributions:
            for c in case_risk.contributions:
                if not any(p.get("type") == c.factor for p in patterns_inferred):
                    sev = "HIGH" if c.points >= 20 else ("MEDIUM" if c.points >= 10 else "LOW")
                    patterns_inferred.append({
                        "type": c.factor,
                        "severity": sev,
                        "explanation": c.explanation,
                        "evidence_txs": c.supporting_transactions
                    })

        # Calculate composite risk score
        risk_score = case_risk.risk_score if case_risk else 0.0
        risk_level = case_risk.risk_category if case_risk else "LOW"
        risk_breakdown = [f"{c.factor}: +{c.points} pts ({c.explanation})" for c in case_risk.contributions] if case_risk else []

        if findings:
            findings_dicts = [
                {
                    "finding_type": f.finding_type,
                    "severity": f.severity.value if hasattr(f.severity, "value") else str(f.severity),
                    "score_delta": f.score_delta,
                    "explanation": f.explanation,
                    "evidence_txs": f.evidence_txs
                }
                for f in findings
            ]
            static_summary = RiskExplainability.compute_risk_score(findings_dicts)
            if static_summary.get("score", 0) > risk_score:
                risk_score = static_summary["score"]
                risk_level = static_summary["level"]
                risk_breakdown = static_summary["reasons"]

        # Initial transaction hash fallback
        init_tx = case.transaction_hash
        if not init_tx and transactions:
            inbound = [t for t in transactions if (t.to_address or "").lower() == norm_suspect]
            if inbound:
                init_tx = inbound[0].transaction_hash
            else:
                init_tx = transactions[0].transaction_hash

        report_id = f"REP-{uuid.uuid4().hex[:8].upper()}"
        title = custom_title or f"Forensic Crypto Investigation Report: {case.complaint_reference}"

        content = {
            "report_metadata": {
                "report_id": report_id,
                "generated_at": datetime.datetime.utcnow().isoformat(),
                "investigator": {
                    "name": investigator_user.full_name,
                    "badge": investigator_user.badge_number,
                    "email": investigator_user.email
                },
                "classification": "CONFIDENTIAL // LAW ENFORCEMENT SENSITIVE"
            },
            "1_case_information": {
                "case_id": case.case_id,
                "complaint_reference": case.complaint_reference,
                "status": case.status.value,
                "priority": case.priority.value,
                "created_at": case.created_at.isoformat(),
                "blockchain": case.blockchain
            },
            "2_incident_summary": {
                "description": case.description or "Victim reported unauthorized cryptocurrency transfer to suspect address.",
                "incident_date": case.incident_date.isoformat(),
                "initial_transaction_hash": init_tx
            },
            "3_victim_information": {
                "name": case.victim_name,
                "reported_loss": f"{case.amount_lost} {case.currency}"
            },
            "4_suspect_wallet": {
                "address": case.suspect_wallet,
                "blockchain": case.blockchain
            },
            "5_transaction_summary": {
                "total_transactions_analyzed": len(transactions),
                "total_flow_native": round(sum(t.amount_native for t in transactions), 4),
                "transactions": [
                    {
                        "tx_hash": t.transaction_hash,
                        "from": t.from_address,
                        "to": t.to_address,
                        "amount": t.amount_native,
                        "timestamp": t.timestamp.isoformat() if t.timestamp else None,
                        "block": t.block_number,
                        "status": t.status
                    }
                    for t in transactions[:20]
                ]
            },
            "6_money_trail": {
                "vasp_paths_found": len(vasp_paths),
                "primary_terminal_path": vasp_paths[0] if vasp_paths else None
            },
            "7_suspicious_patterns_inference": patterns_inferred,
            "8_ai_risk_assessment": {
                "score": risk_score,
                "level": risk_level,
                "breakdown": risk_breakdown
            },
            "9_priority_actionable_wallets": ranked_wallets[:5],
            "10_evidence_locker_references": [
                {
                    "evidence_id": e.evidence_id,
                    "tx_hash": e.transaction_hash,
                    "from": e.from_address,
                    "to": e.to_address,
                    "amount": e.amount,
                    "tag": e.tag,
                    "integrity_hash": e.integrity_hash,
                    "notes": e.investigator_notes
                }
                for e in evidence_items
            ],
            "11_investigator_notes": [
                {
                    "author": n.author.full_name if n.author else "Investigator",
                    "content": n.content,
                    "timestamp": n.created_at.isoformat()
                }
                for n in notes
            ],
            "12_audit_trail": [
                {
                    "action": a.action,
                    "user": a.username,
                    "timestamp": a.timestamp.isoformat()
                }
                for a in audit_records[:15]
            ],
            "13_disclaimer": (
                "FORENSIC NOTICE: Blockchain Fact entries reflect verified cryptographic transactions on the public ledger. "
                "Behavioral patterns and risk metrics represent algorithmic and AI inferences intended to guide investigation priorities "
                "and do not constitute definitive legal proof of fraudulent intent without judicial review."
            )
        }

        # Tamper-evident SHA-256 fingerprint of report payload
        raw_repr = json.dumps(content, sort_keys=True, default=str)
        content["report_metadata"]["integrity_hash_sha256"] = hashlib.sha256(raw_repr.encode("utf-8")).hexdigest()

        report = Report(
            report_id=report_id,
            case_id=case_id,
            title=title,
            content_json=content,
            status=ReportStatus.PENDING_REVIEW,
            generated_at=datetime.datetime.utcnow()
        )
        db.add(report)

        # Update case status
        case.status = "SUPERVISOR_REVIEW"

        # Audit log
        log = AuditLog(
            user_id=investigator_user.id,
            username=investigator_user.username,
            action="REPORT_GENERATED",
            case_id=case_id,
            metadata_json={"report_id": report_id, "title": title, "integrity_hash": content["report_metadata"]["integrity_hash_sha256"]}
        )
        db.add(log)
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def build_json_str(report: Report) -> str:
        return json.dumps(report.content_json, indent=2, default=str)

    @staticmethod
    def build_csv_str(report: Report) -> str:
        output = io.StringIO()
        writer = csv.writer(output)

        content = report.content_json or {}
        writer.writerow(["REPORT_ID", report.report_id])
        writer.writerow(["CASE_ID", report.case_id])
        writer.writerow(["TITLE", report.title])
        writer.writerow(["STATUS", report.status.value if hasattr(report.status, "value") else str(report.status)])
        writer.writerow(["GENERATED_AT", report.generated_at.isoformat() if report.generated_at else ""])
        writer.writerow(["INTEGRITY_HASH", content.get("report_metadata", {}).get("integrity_hash_sha256", "N/A")])
        writer.writerow([])

        # Section: Transactions
        writer.writerow(["--- TRANSACTIONS ANALYZED ---"])
        writer.writerow(["TX_HASH", "FROM_ADDRESS", "TO_ADDRESS", "AMOUNT_ETH", "BLOCK", "TIMESTAMP", "STATUS"])
        txs = content.get("5_transaction_summary", {}).get("transactions", [])
        for tx in txs:
            writer.writerow([
                tx.get("tx_hash", ""),
                tx.get("from", ""),
                tx.get("to", ""),
                tx.get("amount", ""),
                tx.get("block", ""),
                tx.get("timestamp", ""),
                tx.get("status", "")
            ])
        writer.writerow([])

        # Section: Evidence items
        writer.writerow(["--- EVIDENCE ITEMS ---"])
        writer.writerow(["EVIDENCE_ID", "TX_HASH", "FROM", "TO", "AMOUNT", "TAG", "INTEGRITY_HASH"])
        evidence = content.get("10_evidence_locker_references", [])
        for ev in evidence:
            writer.writerow([
                ev.get("evidence_id", ""),
                ev.get("tx_hash", ""),
                ev.get("from", ""),
                ev.get("to", ""),
                ev.get("amount", ""),
                ev.get("tag", ""),
                ev.get("integrity_hash", "")
            ])

        return output.getvalue()

    @staticmethod
    def build_pdf_bytes(report: Report) -> bytes:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "RepTitle",
            parent=styles["Heading1"],
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold"
        )
        section_style = ParagraphStyle(
            "RepSection",
            parent=styles["Heading2"],
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#1e3a8a"),
            fontName="Helvetica-Bold",
            spaceBefore=8,
            spaceAfter=4
        )
        meta_style = ParagraphStyle(
            "RepMeta",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#475569")
        )
        cell_style = ParagraphStyle(
            "RepCell",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#1e293b")
        )
        header_cell_style = ParagraphStyle(
            "RepHeaderCell",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            textColor=colors.white,
            fontName="Helvetica-Bold"
        )
        disclaimer_style = ParagraphStyle(
            "RepDisclaimer",
            parent=styles["Italic"],
            fontSize=7,
            leading=10,
            textColor=colors.HexColor("#64748b")
        )

        content = report.content_json or {}
        elements = []

        # Header Badge
        elements.append(Paragraph("<b>SIH26183 FORENSIC BLOCKCHAIN ANALYTICS // OFFICIAL INVESTIGATION REPORT</b>", meta_style))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(report.title, title_style))
        elements.append(Spacer(1, 6))

        # Metadata Table
        rep_meta = content.get("report_metadata", {})
        investigator = rep_meta.get("investigator", {})
        meta_data = [
            [
                Paragraph(f"<b>Report ID:</b> {report.report_id}", cell_style),
                Paragraph(f"<b>Case ID:</b> {report.case_id}", cell_style)
            ],
            [
                Paragraph(f"<b>Date:</b> {str(rep_meta.get('generated_at', 'N/A'))[:19]}", cell_style),
                Paragraph(f"<b>Investigator:</b> {investigator.get('name', 'N/A')} (Badge: {investigator.get('badge', 'N/A')})", cell_style)
            ],
            [
                Paragraph(f"<b>Classification:</b> {rep_meta.get('classification', 'CONFIDENTIAL')}", cell_style),
                Paragraph(f"<b>Integrity SHA-256:</b> {str(rep_meta.get('integrity_hash_sha256', 'N/A'))[:24]}...", cell_style)
            ]
        ]
        meta_table = Table(meta_data, colWidths=[260, 280])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 8))

        # Section 1: Incident & Subject Profile
        elements.append(Paragraph("1. Incident & Subject Profile", section_style))
        victim_info = content.get("3_victim_information", {})
        suspect_info = content.get("4_suspect_wallet", {})

        info_data = [
            [
                Paragraph(f"<b>Victim Name:</b> {victim_info.get('name', 'N/A')}", cell_style),
                Paragraph(f"<b>Reported Loss:</b> {victim_info.get('reported_loss', 'N/A')}", cell_style)
            ],
            [
                Paragraph(f"<b>Suspect Wallet:</b> {suspect_info.get('address', 'N/A')}", cell_style),
                Paragraph(f"<b>Blockchain:</b> {suspect_info.get('blockchain', 'Ethereum')}", cell_style)
            ]
        ]
        info_table = Table(info_data, colWidths=[260, 280])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#ffffff")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 8))

        # Section 2: AI Risk Assessment & Findings
        elements.append(Paragraph("2. Algorithmic Risk Assessment & Behavioral Inferences", section_style))
        risk_data = content.get("8_ai_risk_assessment", {})
        score = risk_data.get("score", 0)
        level = risk_data.get("level", "LOW")

        elements.append(Paragraph(
            f"<b>Composite Risk Score:</b> {score:.1f} / 100.0 &nbsp;|&nbsp; <b>Risk Tier:</b> {level}",
            cell_style
        ))
        elements.append(Spacer(1, 4))

        findings = content.get("7_suspicious_patterns_inference", [])
        if findings:
            f_rows = [[
                Paragraph("<b>Finding Type</b>", header_cell_style),
                Paragraph("<b>Severity</b>", header_cell_style),
                Paragraph("<b>Explanation</b>", header_cell_style)
            ]]
            for f in findings[:5]:
                f_rows.append([
                    Paragraph(str(f.get("type", "N/A")), cell_style),
                    Paragraph(str(f.get("severity", "MEDIUM")), cell_style),
                    Paragraph(str(f.get("explanation", "N/A"))[:120], cell_style)
                ])
            f_table = Table(f_rows, colWidths=[130, 80, 330])
            f_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(f_table)
        elements.append(Spacer(1, 8))

        # Section 3: Money Trail
        elements.append(Paragraph("3. Multi-Hop Money Trail & Attributed VASP Exits", section_style))
        trail_info = content.get("6_money_trail", {})
        vasp_count = trail_info.get("vasp_paths_found", 0)
        elements.append(Paragraph(
            f"<b>Attributed VASP / Exchange Exit Paths Found:</b> {vasp_count}",
            cell_style
        ))
        elements.append(Spacer(1, 8))

        # Section 4: Key Transactions
        elements.append(Paragraph("4. Analyzed Cryptographic Ledger Transactions", section_style))
        txs = content.get("5_transaction_summary", {}).get("transactions", [])
        if txs:
            t_rows = [[
                Paragraph("<b>Tx Hash</b>", header_cell_style),
                Paragraph("<b>From</b>", header_cell_style),
                Paragraph("<b>To</b>", header_cell_style),
                Paragraph("<b>Amount</b>", header_cell_style),
                Paragraph("<b>Block</b>", header_cell_style)
            ]]
            for tx in txs[:6]:
                t_rows.append([
                    Paragraph(str(tx.get("tx_hash", ""))[:14] + "...", cell_style),
                    Paragraph(str(tx.get("from", ""))[:12] + "...", cell_style),
                    Paragraph(str(tx.get("to", ""))[:12] + "...", cell_style),
                    Paragraph(f"{float(tx.get('amount', 0)):.4f} ETH", cell_style),
                    Paragraph(str(tx.get("block", "N/A")), cell_style)
                ])
            t_table = Table(t_rows, colWidths=[120, 110, 110, 100, 100])
            t_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(t_table)
        elements.append(Spacer(1, 8))

        # Section 5: Legal Disclaimer & Cryptographic Fingerprint
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceBefore=6, spaceAfter=6))
        disclaimer_text = content.get("13_disclaimer", "")
        elements.append(Paragraph(f"<b>FORENSIC NOTICE:</b> {disclaimer_text}", disclaimer_style))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(
            f"<b>Cryptographic Verification:</b> SHA-256 Digest = <code>{rep_meta.get('integrity_hash_sha256', 'N/A')}</code>",
            disclaimer_style
        ))

        doc.build(elements)
        return buffer.getvalue()

