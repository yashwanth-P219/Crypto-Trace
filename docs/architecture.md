# System Architecture: SIH26183 Cryptocurrency Fraud Investigation Platform

## Overview
The platform provides law enforcement, financial intelligence units (FIUs), and cybercrime investigators with an automated, explainable system for tracing stolen cryptocurrency assets across multi-hop transactions to identifying destination Virtual Asset Service Providers (VASPs / Centralized Exchanges).

```
+-------------------------------------------------------------------------------+
|                       React + TypeScript Frontend                             |
|   (Investigation Command Center, Interactive Graph, Money Trail, Copilot)     |
+-------------------------------------------------------------------------------+
                                      |
                                  REST / JSON
                                      v
+-------------------------------------------------------------------------------+
|                        FastAPI Forensic Backend                               |
|   +-------------------+  +--------------------+  +------------------------+   |
|   | Auth & RBAC (JWT) |  | Case Management    |  | Evidence Locker        |   |
|   +-------------------+  +--------------------+  +------------------------+   |
|   +-------------------+  +--------------------+  +------------------------+   |
|   | Watchlist & Alert |  | Forensic Reports   |  | Audit Trail Logging    |   |
|   +-------------------+  +--------------------+  +------------------------+   |
+-------------------------------------------------------------------------------+
             |                                    |
             v                                    v
+-----------------------------+     +-----------------------------+
|    Blockchain Abstraction   |     |    PostgreSQL / SQLite      |
|  - Ethereum Sepolia         |     |  - Cases, Wallets, Txs      |
|  - Ethereum Mainnet (R/O)   |     |  - Evidence SHA-256 Hashes  |
|  - Polygon PoS Architecture |     |  - Address Labels & Audits  |
|  - BNB Chain Architecture   |     +-----------------------------+
|  - Cross-Chain Bridge Intel |
+-----------------------------+
             |
             v
+-------------------------------------------------------------------------------+
|                          Analytics & Intelligence                             |
|  +-------------------------------------------------------------------------+  |
|  | NetworkX Graph Analytics (Multi-Hop BFS, VASP Shortest Paths, Cycles)   |  |
|  +-------------------------------------------------------------------------+  |
|  | Suspicious Pattern Heuristics (Rapid Exit, Peeling Structuring, Bursts) |  |
|  +-------------------------------------------------------------------------+  |
|  | Explainable Risk Scoring (0-100 Score with Linked Evidence Tx Hashes)   |  |
|  +-------------------------------------------------------------------------+  |
|  | Priority Engine (Multi-criteria Ranking of 500+ Wallets for Subpoena)  |  |
|  +-------------------------------------------------------------------------+  |
|  | Investigation Copilot (Context-Grounded Q&A over Verified Case Ledger)  |  |
|  +-------------------------------------------------------------------------+  |
+-------------------------------------------------------------------------------+
```

---

## 4-Tier Truth Taxonomy
To ensure judicial credibility and evidentiary admissibility, the platform strictly categorizes all output:

| Truth Level | Color Code | Description | Example |
| :--- | :--- | :--- | :--- |
| **`BLOCKCHAIN FACT`** | Emerald / Cyan | Verifiable cryptographic ledger facts | "Wallet A sent 2.48 ETH to Wallet B in block 19451040" |
| **`SYSTEM INFERENCE`** | Amber / Yellow | Algorithmic behavioral pattern flags | "Rapid transfer detected: funds dispersed within 8 mins" |
| **`AI ASSESSMENT`** | Purple / Violet | Machine learning risk rankings & suggestions | "Wallet G prioritized #1 due to direct VASP liquidation" |
| **`INVESTIGATOR DECISION`** | Blue / Indigo | Officer actions, tags, and sign-offs | "Supervisor Sunita Rao approved report for Section 91 CrPC" |

---

## Data Pipeline
1. **Intake**: Victim or investigator submits suspect address, incident date, and amount lost.
2. **Retrieval**: System queries provider abstraction (Ethereum Sepolia, Mainnet, Polygon, BNB) or indexed SQLite/Postgres ledger.
3. **Normalization**: Raw RPC responses standardized into `NormalizedTx` schema with native amounts, gas, and USD conversion.
4. **Graph Construction**: NetworkX directed multigraph models addresses as nodes and transactions as edges.
5. **Multi-Hop Traversal**: Path analyzer discovers liquidation routes terminating at recognized VASPs (e.g. Binance, CoinDCX, WazirX).
6. **Pattern Evaluation**: 11 forensic heuristic rules scan for structuring, peeling chains, and burst volumes.
7. **Priority Ranking**: Candidate addresses scored and ranked by proximity, flow amount, and exchange reachability.
8. **Evidence Preservation**: Important hops saved with SHA-256 integrity hashes to prevent evidentiary tampering.
