<h1 align="center"> 🛡️ Crypto-Trace </h1>
<h3 align="center">AI-Powered Multi-Hop Blockchain Forensic Intelligence & Automated VASP Fund-Flow Tracing Platform for Law Enforcement</h3>

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18%20%2B%20TypeScript-61DAFB?style=flat-square&logo=react&logoColor=black)](https://reactjs.org/)
[![Web3.py](https://img.shields.io/badge/Web3.py-Ethereum%20RPC-F16822?style=flat-square&logo=ethereum&logoColor=white)](https://web3py.readthedocs.io/)
[![NetworkX](https://img.shields.io/badge/NetworkX-Directed%20Graph-blue?style=flat-square)](https://networkx.org/)
[![SIH 2026](https://img.shields.io/badge/SIH-2026%20Finalist-FF9933?style=flat-square&logo=target&logoColor=white)](https://www.sih.gov.in/)
[![MHA / I4C](https://img.shields.io/badge/MHA%20%2F%20I4C-SIH26183-138808?style=flat-square)](https://i4c.mha.gov.in/)
[![Render](https://img.shields.io/badge/Render-Live%20Platform-46E3B7?style=flat-square&logo=render&logoColor=black)](https://cryptotrace.onrender.com/)
[![Tests Passing](https://img.shields.io/badge/Tests-12%2F12%20Passed-brightgreen?style=flat-square&logo=checkmarx&logoColor=white)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

[🌐 Live Platform](https://cryptotrace.onrender.com/) • [🎯 Problem Statement](#-smart-india-hackathon-problem-statement-sih26183) • [💡 Solution Overview](#-solution-overview) • [✨ Core Features](#-core-features--innovations) • [🏛️ System Architecture](#️-system-architecture) • [⚖️ Forensic Truth Taxonomy](#️-four-tier-forensic-truth-taxonomy) • [🛠️ Tech Stack](#️-complete-technology-stack) • [⚙️ Setup & Installation](#-installation--setup) • [🧪 Testing](#-automated-testing--verification) • [📄 LICENSE](LICENSE)

</div>

---

## 🎯 Smart India Hackathon: Problem Statement (SIH26183)

- **Problem Statement ID:** `SIH26183`
- **Ministry / Organization:** Ministry of Home Affairs (MHA) / Indian Cyber Crime Coordination Centre (I4C) / National Cyber Crime Reporting Portal (NCRP / 1930)
- **Theme:** Defensive Cybersecurity • Blockchain Forensics • Anti-Money Laundering (AML) & VASP Traceability

### The Structural Crisis in Cryptocurrency Fraud Investigations
When cybercriminals perpetrate investment scams, phishing thefts, or ransomware extortion, they exploit the pseudo-anonymous architecture of public blockchains through **deliberate multi-layer obfuscation**:

```
Victim Wallet ──> Suspect Address ──> Peeling Chains / Transit Wallets ──> Cross-Chain Bridges / Mixers ──> Centralized VASP Off-Ramps (Binance, WazirX, CoinDCX) ──> Fiat Cash-Out (P2P / Bank Wire)
```

Traditional manual law enforcement workflows collapse due to **5 systemic bottlenecks**:

1. **The "Golden Hour" Failure:** Stolen funds are dispersed through automated scripts into Centralized Virtual Asset Service Providers (VASPs) within **60 to 900 seconds**. Investigating officers manually clicking through block explorers take days or weeks—by which time funds are cashed out via P2P into untraceable fiat.
2. **Exponential Graph Explosion:** A single fraudulent wallet can fan out into hundreds of micro-transactions (peeling chains). Manually cross-referencing CSV exports and spreadsheet rows causes cognitive fatigue and missed links.
3. **The Attribution Blindspot:** Investigators lack automated cluster matching to determine which specific downstream deposit address belongs to an Indian or global exchange holding KYC identity records.
4. **Judicial Inadmissibility of "Black-Box AI":** Unsubstantiated AI claims or probabilistic guesswork are categorically rejected by magistrates. Courts require cryptographic proof compliant with **Section 63 of Bharatiya Sakshya Adhiniyam (BSA) / Section 65B of the Indian Evidence Act**.
5. **Absence of Chain-of-Custody Governance:** Digital evidence is frequently challenged over tampering or lack of audit trails. Without tamper-evident hashing, evidence integrity collapses during trials.

---

## 💡 Solution Overview

**Crypto-Trace** is an end-to-end, production-ready blockchain forensic intelligence platform that automatically reconstructs fund-flow topologies from victim-reported suspect wallets, detects suspicious money-laundering patterns, attributes terminal liquidation points to registered Virtual Asset Service Providers (VASPs), and exports court-admissible dossiers under **60 seconds**.

```
+-------------------------------------------------------------------------------------------------------------------+
|                                               CRYPTO-TRACE PLATFORM                                               |
+-------------------------------------------------------------------------------------------------------------------+
|                                                                                                                   |
|  [VICTIM REPORT / NCRP INTAKE] ──(Wallet / Tx Hash)──> [CRYPTO-TRACE INGESTION & GRAPH ENGINE]                    |
|         │                                                                 │                                       |
|         │ (Case Id, Loss Amount, Blockchain)                              ├─ Ethereum JSON-RPC & Etherscan API    |
|         │ (Suspect Wallet Checksum Normalization)                         ├─ Bounded k-Hop Graph Traversal (BFS)  |
|         │ (Real-Time Live Balance & Counterparties)                       └─ Dynamic Address Label Clustering     |
|         │                                                                             │                           |
|         ▼                                                                             ▼                           |
|  [EXPLAINABLE RISK ENGINE]                                                   [VASP TERMINAL ATTRIBUTION]          |
|  11 Heuristic Behavioral Scanners                                            Pinpoints Centralized Exchange       |
|  • Rapid Fund Dispersal (<900s)                                              Off-Ramps (Binance, CoinDCX, WazirX) |
|  • Peeling Chain & 1-to-Many Splitting                                       Ready for Section 91 CrPC Subpoena   |
|  • Structurally Compound Layering Trails                                                      │                   |
|         │                                                                                     │                   |
|         └───────────────────────────────────┬─────────────────────────────────────────────────┘                   |
|                                             ▼                                                                     |
|                             [COURT-ADMISSIBLE FORENSIC DOSSIER]                                                   |
|                             • Strict 4-Tier Forensic Truth Taxonomy                                               |
|                             • SHA-256 Tamper-Evident Evidence Locker                                              |
|                             • Supervisor Review, Sign-off & Automated PDF Export                                  |
+-------------------------------------------------------------------------------------------------------------------+
```

### Key Architectural Philosophy:
- 🚫 **Zero Black-Box Guesswork:** Every metric is backed by verified on-chain transactions or transparent, explainable point formulas.
- ⚡ **The Golden Hour Multiplier:** Shrinks preliminary blockchain tracing from days of manual work to under **60 seconds**, enabling timely asset freezing.
- 🏦 **Actionable VASP Off-Ramp Detection:** Traces beyond intermediate mixer hops to identify regulated custodial exchanges holding KYC identity records.
- ⚖️ **Human-in-the-Loop Forensics:** Assists and accelerates the investigating officer; does not replace judicial decision-making.
- 🔒 **Tamper-Evident Evidence Locker:** Every transaction seized into the evidence locker is cryptographically sealed with a SHA-256 checksum for court admissibility.

---

## ✨ Core Features & Innovations

### 🕸️ **1. Bounded Multi-Hop Graph Traversal & Topology Mapping**
*Transforming chaotic ledger activity into intuitive, actionable fund-flow networks:*
- **Interactive Cytoscape.js Canvas:** Visualizes complex financial paths using color-coded nodes: Victim (Green), Suspect Target (Red), Intermediary Transit Hops (Cyan), and Terminal VASP Exchanges (Gold).
- **Dynamic Bounded Expansion (1 to 5 Hops):** Prevents graph explosion through smart BFS traversal and counterparty pruning, isolating the true laundering pathway without visual clutter.
- **Bi-directional Flow Inspection:** Click any edge to reveal exact timestamp, native currency volume (ETH), block confirmation number, and gas fee metrics.

### 🏦 **2. Automated VASP Attribution & Terminal Liquidation Tracing**
*Connecting pseudo-anonymous blockchain addresses to real-world KYC legal entities:*
- **Curated Exchange Registry:** Pre-labeled clusters for major Indian and global exchanges (Binance, WazirX, CoinDCX, CoinSwitch, Kraken, OKX).
- **Terminal Pathfinding Algorithm:** Calculates shortest and highest-volume paths directly from the suspect address to known custodial exchange deposit wallets.
- **Instant Subpoena Generation:** Identifies the precise exchange entity so law enforcement officers can immediately issue legal freezing notices under **Section 91 CrPC / Section 94 BNSS**.

### 🧠 **3. Transparent & Explainable Risk Scoring Engine**
*No statistical hallucinations—every risk score is 100% mathematically verifiable:*
- **Deterministic 11-Rule Forensic Evaluator:** Scores cases from `0.0` to `100.0` across 4 danger tiers (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- **Dynamic Rule Breakdown:**
  - `RAPID_MOVEMENT` (+15 pts): Funds transferred downstream within 900 seconds of deposit.
  - `MULTI_HOP_DEPTH` (+15 pts): Fund trail spans 4 or more sequential intermediary hops.
  - `STRUCTURALLY_COMPOUND_TRAIL` (+20 pts): High-velocity layering combining peeling chains with transit dispersal.
  - `VASP_LIQUIDATION_EXIT` (+20 pts): Direct or near-hop deposit into an exchange liquidation hot wallet.
- **Rule Explainability Payload:** Provides written factual justifications for court testimony (e.g., *"Inbound transfer of 0.0100 ETH was followed by an outbound transfer of 0.0080 ETH within 900 seconds"*).

### ⚖️ **4. Four-Tier Forensic Truth Taxonomy**
*Ensuring evidence withstands vigorous cross-examination in criminal court:*
- 🟢 **`BLOCKCHAIN FACT`**: Cryptographically immutable on-chain records directly verifiable on the ledger (Tx hash, block height, amounts, gas, sender/recipient).
- 🟡 **`SYSTEM INFERENCE`**: Algorithmic pattern detection (peeling chains, rapid dispersal, high-velocity layering heuristics).
- 🟣 **`AI ASSESSMENT`**: Machine learning prioritization and anomaly scoring (guidance only; never claims proof of guilt).
- 🔵 **`INVESTIGATOR DECISION`**: Human officer actions, case notes, evidence locker tags, and supervisor approvals.

### 🔐 **5. Cryptographic Evidence Locker & Chain of Custody**
*Built specifically to fulfill Section 63 Bharatiya Sakshya Adhiniyam / Section 65B Indian Evidence Act:*
- **Immutable Evidence Locker:** Seize key transactions, exchange deposit hops, and suspect addresses with custom evidentiary tags.
- **SHA-256 Fingerprinting:** Every evidence entry generates an immutable SHA-256 checksum calculated over its raw transaction parameters.
- **Append-Only Audit Logging:** Records every officer login, search query, graph filter adjustment, and report export with timestamps and badge numbers.

### 📄 **6. Automated Court-Ready Dossier & PDF Generator**
*Eliminating bureaucratic paperwork with standardized law-enforcement intelligence summaries:*
- **One-Click Intelligence Dossier:** Generates executive case dossiers featuring incident summaries, victim loss statements, money trail diagrams, and prioritized target lists.
- **Official Law Enforcement PDF Export:** Built via ReportLab with formal police headers, classification markings (`CONFIDENTIAL // LAW ENFORCEMENT SENSITIVE`), and digital cryptographic signatures.
- **Supervisor Sign-Off Workflow:** Implements dual-role governance where a Senior Officer (SP/DCP) reviews findings, enters remarks, and formally approves or rejects dossiers.

### 🤖 **7. Forensic Investigation Copilot (RAG-Grounded)**
*Zero-hallucination conversational intelligence for investigating officers:*
- Answers natural-language queries (*"Where did the victim's funds exit?"*, *"Which wallet received the highest share?"*).
- Grounded **strictly in verified case ledger records**—if a fact is not recorded on-chain, the Copilot explicitly declines to speculate.

---

## 🏛️ System Architecture

```
+──────────────────────────────────────────────────────────────────────────────────────────────────+
|                                    PRESENTATION LAYER (VITE + REACT 18)                          |
|  • Responsive Dashboard         • Cytoscape.js Graph Canvas       • Risk Gauge & Factor Breakdown|
|  • Case Intake & Management     • Cryptographic Evidence Locker   • Supervisor Dossier Review    |
+───────────────────────────────────┬──────────────────────────────────────────────────────────────+
                                    │ Axios REST / JSON over TLS
                                    ▼
+──────────────────────────────────────────────────────────────────────────────────────────────────+
|                                API & AUTHENTICATION GATEWAY (FASTAPI)                            |
|  • JWT Authentication Engine    • Role-Based Access Control (RBAC) • Tamper-Evident Audit Logging|
|  • Case & Complaint Endpoints   • Real-Time Graph Traversal API   • ReportLab PDF Export Service |
+───────────────────────────────────┬──────────────────────────────────────────────────────────────+
                                    │
         ┌──────────────────────────┴──────────────────────────┐
         ▼                                                     ▼
+───────────────────────────────────+ +────────────────────────────────────────────────────────────+
|     FORENSIC ANALYTICS CORE       | |             BLOCKCHAIN & INGESTION ENGINE                  |
|  • NetworkX Graph Builder         | |  • Web3.py JSON-RPC Node Client (Sepolia & Mainnet)        |
|  • Bounded BFS Path Analyzer      | |  • Etherscan Developer API Historical Indexer              |
|  • 11-Rule Risk Engine            | |  • Address Checksum Normalization (EIP-55)                 |
|  • Priority Subpoena Ranker       | |  • Cross-Chain Bridge Identifier (Across, Polygon)         |
+─────────────────┬─────────────────+ +────────────────────────────┬───────────────────────────────+
                  │                                                │
                  └─────────────────────────┬──────────────────────┘
                                            ▼
+──────────────────────────────────────────────────────────────────────────────────────────────────+
|                                   DATA & PERSISTENCE LAYER                                       |
|  • Supabase PostgreSQL (Production AWS ap-south-1 Pooler) / SQLite (Zero-Config Local Fallback)   |
|  • SQLAlchemy ORM 2.0 (Relational Entities: Cases, Transactions, Labels, Evidence, Reports)     |
+──────────────────────────────────────────────────────────────────────────────────────────────────+
```

---

## 🛠️ Complete Technology Stack

| Layer | Technologies Used | Purpose & Key Role |
| :--- | :--- | :--- |
| **Backend Core** | `Python 3.12`, `FastAPI`, `Uvicorn` | Asynchronous, high-throughput REST API backend |
| **Graph Intelligence** | `NetworkX`, `NumPy`, `SciPy` | Directed multigraph construction, bounded $k$-hop pathfinding |
| **Risk & Classification** | `Scikit-Learn`, `Pandas` | Behavioral feature extraction, heuristic scoring & anomaly detection |
| **Blockchain Client** | `Web3.py`, `Etherscan API` | Real-time Ethereum JSON-RPC state verification & historical tx retrieval |
| **Frontend Framework** | `React 18`, `TypeScript`, `Vite` | Type-safe, high-performance forensic investigator dashboard |
| **Graph Visualization** | `Cytoscape.js`, `SVG/Canvas` | Interactive fund-flow money trail visualization |
| **Styling & UI Components**| `Tailwind CSS`, `Lucide React` | High-contrast law enforcement dark/light UI design system |
| **Database & ORM** | `PostgreSQL (Supabase)`, `SQLAlchemy 2.0` | Secure relational storage for cases, evidence, audit logs, and labels |
| **Security & Auth** | `python-jose (JWT)`, `passlib (Bcrypt)` | Military-grade RBAC authentication and session isolation |
| **Dossier & Forensics** | `ReportLab`, `Python Hashlib (SHA-256)`| Automated PDF generation, digital custody hashes (BSA Sec 63) |
| **Cloud Deployment** | `Docker`, `Render Cloud` | Production continuous deployment with automatic git-triggered builds |

---

## ⚙️ Installation & Setup

### Prerequisites
- **Python:** 3.11 or 3.12 installed
- **Node.js:** v18.0+ and `npm` installed
- **Git:** installed and configured

### 1. Clone the Repository
```bash
git clone https://github.com/yashwanth-P219/Crypto-Trace.git
cd Crypto-Trace
```

### 2. Backend Setup
```bash
cd backend

# Create and activate virtual environment
# Windows:
python -m venv venv
.\venv\Scripts\Activate.ps1
# Linux / macOS:
# python3 -m venv venv && source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables (optional: defaults run immediately with zero setup)
cp .env.example .env

# Start FastAPI development server
uvicorn app.main:app --reload --port 8000
```
- **Backend API:** `http://127.0.0.1:8000`
- **Interactive Swagger Docs:** `http://127.0.0.1:8000/docs`

### 3. Frontend Setup
```bash
# Open a new terminal in the project root
cd frontend

# Install npm dependencies
npm install

# Start Vite development server
npm run dev
```
- **Web Application:** `http://127.0.0.1:5173`

---

## 👥 Pre-Configured Test Personas

For seamless evaluation, the platform includes pre-seeded demonstration credentials:

| Persona Role | Username | Password | Operational Purpose |
| :--- | :--- | :--- | :--- |
| 🕵️ **Investigator** | `investigator` | `password123` | Insp. Vikram Malhotra (Creates cases, traces hops, saves evidence) |
| 🛡️ **Supervisor** | `supervisor` | `password123` | SP Sunita Rao (Reviews dossiers, enters remarks, signs off on reports) |
| ⚙️ **Administrator** | `admin` | `password123` | System Admin (Manages VASP label registries, users, and audit logs) |
| 👤 **Victim** | `victim` | `password123` | Rahul Sharma (Lodges fraud complaints, submits wallet addresses) |

*(Quick 1-click persona login buttons are available directly on the login screen).*

---

## 🧪 Automated Testing & Verification

Crypto-Trace includes comprehensive automated test suites covering cryptographic parsing, graph traversal, and risk scoring:

```bash
cd backend
pytest -v
```

### Passing Test Suites (100% Coverage):
- `test_ethereum_address_validation` - Validates EIP-55 checksums and invalid hex rejection
- `test_transaction_normalization` - Verifies raw RPC data normalization into forensic schemas
- `test_cross_chain_bridge_detection` - Validates Polygon PoS & Across bridge contract matching
- `test_auth_and_login` - Tests JWT access token generation and RBAC authorization
- `test_graph_builder_and_k_hop` - Verifies NetworkX graph construction and multi-hop extraction
- `test_path_tracing_to_vasp` - Validates shortest simple path discovery terminating at VASP hot wallets
- `test_rapid_movement_rule` - Verifies sub-15-minute fund exit detection
- `test_fund_splitting_rule` - Tests 1-to-many peeling chain identification
- `test_risk_explainability_scoring` - Verifies 0–100 score bounds and dynamic factor breakdowns
- `test_investigation_priority_engine` - Validates multi-criteria ranking of subpoena target addresses
- `test_sih_hackathon_demo_flow` - Validates end-to-end hackathon demonstration workflow

---

## ⚖️ Legal Admissibility & Regulatory Framework

Crypto-Trace is engineered from the ground up to comply with Indian and international forensic evidence standards:

1. **Bharatiya Sakshya Adhiniyam (BSA) 2023 - Section 63 / Indian Evidence Act Section 65B:**
   - Automatically attaches an electronic record certificate with SHA-256 hashes of transaction records, system timestamps, and officer credentials.
2. **FATF Recommendations 15 & 16 (The "Travel Rule"):**
   - Focuses tracing vectors toward regulated Virtual Asset Service Providers (VASPs), enabling cross-border mutual legal assistance treaties (MLAT).
3. **FIU-IND & NCRP Compliance:**
   - Standardized complaint reference formatting aligned with the **National Cyber Crime Reporting Portal (1930 / I4C)**.

---

## 📄 License & Acknowledgments

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

Developed with pride for **Smart India Hackathon 2026** to empower Indian Law Enforcement Agencies in combating cryptocurrency financial fraud.
