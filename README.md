# SIH26183: Real-Time Identification of Fraud-Linked Cryptocurrency Exchanges from Victim-Reported Suspect Wallet Addresses through Automated Blockchain Analytics

[![Smart India Hackathon 2026](https://img.shields.io/badge/SIH-2026-blue.svg)](https://www.sih.gov.in/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%20%2B%20Vite%20%2B%20TS-61DAFB.svg)](https://reactjs.org/)
[![Web3.py](https://img.shields.io/badge/Blockchain-Web3.py%20%2B%20Sepolia-orange.svg)](https://web3py.readthedocs.io/)
[![Tests](https://img.shields.io/badge/Tests-12%20Passed-brightgreen.svg)]()

> **Problem Statement ID**: SIH26183  
> **Platform Category**: Defensive Cybercrime & Digital Asset Forensics  
> **Target End Users**: Cybercrime Police Officers, Financial Intelligence Units (FIU-IND), and Digital Forensic Investigators.

---

## 1. Executive Summary & Objective
When a victim loses funds in cryptocurrency fraud (phishing, impersonation, high-yield investment scams), cybercrime units face a critical roadblock: perpetrators rapidly route assets through complex multi-hop layering chains, peeling wallets, and cross-chain bridges before liquidating them into Centralized Virtual Asset Service Providers (VASPs / Exchanges).

This platform empowers investigators to:
1. Intake victim fraud reports and suspect wallet addresses.
2. Automate multi-hop transaction graph traversal (1, 2, 3, 5 hops).
3. Discover verified liquidation paths terminating at recognized VASPs (e.g. Binance, CoinDCX, WazirX).
4. Evaluate 11 explainable behavioral heuristics (peeling chains, fund splitting, rapid exits, transit consolidation).
5. Generate an explainable **Investigation Risk Score (0–100)** tied to cryptographic transaction evidence.
6. Rank candidate wallets using an **Investigation Priority Engine** to prioritize KYC subpoenas.
7. Query an **Investigation Copilot** that answers questions strictly using verified case ledger facts with zero hallucination.
8. Preserve digital evidence with **SHA-256 cryptographic integrity hashes**.
9. Generate police-standard forensic dossiers with a **Supervisor Review & Sign-Off workflow**.

---

## 2. Four-Tier Truth Taxonomy
To ensure judicial credibility and admissibility in criminal court:

- **`BLOCKCHAIN FACT`**: Cryptographically verifiable on-chain facts (Tx hash, block number, amount, timestamp, from/to address).
- **`SYSTEM INFERENCE`**: Algorithmic pattern detection (rapid fund movement, fund splitting structuring, multi-hop hops).
- **`AI ASSESSMENT`**: Machine learning anomaly scores and priority recommendations (guidance only; never claims proof of guilt).
- **`INVESTIGATOR DECISION`**: Officer actions, evidence tags, case state transitions, and supervisor sign-offs.

---

## 3. Technology Stack

- **Backend**: Python 3.12, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2 (SQLite zero-setup default with PostgreSQL support), python-jose (JWT Auth), passlib (Bcrypt).
- **Blockchain**: Web3.py, resilient RPC provider abstraction supporting **Ethereum Sepolia testnet**, **Ethereum Mainnet (R/O)**, **Polygon PoS**, and **BNB Smart Chain**, with Cross-Chain Bridge detection.
- **Graph & Risk Analytics**: NetworkX directed multigraphs, 11 heuristic forensic rules, scikit-learn Random Forest Classifier.
- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, Lucide React icons, interactive SVG/Canvas transaction graph with multi-hop filters and node/edge inspection drawers.
- **Testing**: pytest (12 automated unit and end-to-end integration tests).

---

## 4. Quickstart Guide (Local Run)

### Backend

```bash
# 1. Open terminal and navigate to backend
cd backend

# 2. Virtual environment is pre-configured in backend/venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
# source venv/bin/activate

# 3. Run FastAPI backend server
uvicorn app.main:app --reload --port 8000
```

- API Base URL: `http://127.0.0.1:8000`
- Interactive Swagger / OpenAPI Docs: `http://127.0.0.1:8000/docs`

### Frontend

```bash
# 1. Open a second terminal and navigate to frontend
cd frontend

# 2. Start Vite development server
npm run dev
```

- Web Dashboard URL: `http://127.0.0.1:5173`

---

## 5. Running Automated Test Suite

```bash
cd backend
.\venv\Scripts\pytest -v
```

All 12 tests pass cleanly:
- `test_ethereum_address_validation` - Checksum and hex format validation
- `test_transaction_normalization` - Raw RPC data normalization schema
- `test_cross_chain_bridge_detection` - Polygon PoS & Across bridge contract matching
- `test_health_and_status` - System health check
- `test_auth_and_login` - JWT generation and RBAC authorization
- `test_graph_builder_and_k_hop` - NetworkX graph construction and 1-hop / 3-hop extraction
- `test_path_tracing_to_vasp` - Shortest simple path discovery to VASP
- `test_rapid_movement_rule` - Sub-15 minute exit heuristic
- `test_fund_splitting_rule` - 1-to-many peeling chain heuristic
- `test_risk_explainability_scoring` - 0-100 score cap and reason breakdown
- `test_investigation_priority_engine` - Multi-criteria ranking of target addresses
- `test_sih_hackathon_demo_flow` - Full end-to-end hackathon workflow

---

## 6. Pre-Configured Test Accounts

| Role | Username | Password | Purpose |
| :--- | :--- | :--- | :--- |
| **Investigator** | `investigator` | `password123` | Insp. Vikram Malhotra (Creates cases, traces hops, saves evidence) |
| **Supervisor** | `supervisor` | `password123` | SP Sunita Rao (Reviews & approves/rejects forensic reports) |
| **Administrator**| `admin` | `password123` | System Administrator (Manages VASP labels & configuration) |
| **Victim** | `victim` | `password123` | Rahul Sharma (Submits fraud complaint & tracks progress) |

*(Quick 1-click login buttons are provided directly on the login screen for instant evaluation).*

---

## 7. Official SIH Hackathon Demo Scenario

The application includes an official built-in SIH Hackathon scenario:

### The Scenario
- **Victim**: Rahul Sharma
- **Reported Loss**: ₹5,00,000 (2.50 ETH)
- **Complaint Ref**: `CR-2026-DEL-8942`
- **Suspect Intake Wallet**: `0x4838B106FCe9647Bdf1E7877BF73cE8B0BAD5f97`

### The Money Trail
```
Victim (Rahul Sharma)
   │
   ▼ 2.50 ETH (Initial Theft Deposit)
Wallet A (Suspect Intake: 0x4838B106...)
   │
   ▼ 2.48 ETH (Rapid movement after 8 mins)
Wallet B (Fund Splitting Hub: 0x1Db3439...)
   │
   ├────── 1.20 ETH ──────► Wallet F (Money Mule: 0x0d4a11...)
   │                           │
   │                           ▼ 1.18 ETH (Consolidation)
   │                        Wallet G (Suspect Hub: 0x7a250d...)
   │                           │
   │                           ▼ 1.15 ETH (Terminal Liquidation)
   │                        Binance 14 (Hot Wallet: 0x28C6c062...) 🏦
   │
   ├────── 0.80 ETH ──────► Wallet C (Intermediary Split)
   │
   └────── 0.48 ETH ──────► Wallet D (Intermediary Split)
```

### Forensic Findings
- **Risk Score**: `91/100 HIGH`
- **Detected Patterns**:
  1. `RAPID_MOVEMENT` (+15): Dispersed within 8 minutes of deposit.
  2. `FUND_SPLITTING` (+15): Layering into 3 distinct downstream addresses.
  3. `MULTI_HOP_DEPTH` (+15): Trail spans 4 distinct hops.
  4. `VASP_LIQUIDATION_EXIT` (+20): 1.15 ETH deposited into Binance Hot Wallet.
  5. `UNUSUAL_TRANSACTION_BURST` (+10): Completed in under 45 minutes.
  6. `SUDDEN_LARGE_TRANSFER` (+16): 2.50 ETH abnormal entry.
- **Priority Engine**:
  - **Rank 1**: Wallet G (Direct exit into Binance VASP hot wallet — subpoena target).
  - **Rank 2**: Wallet B (Primary peeling chain distribution hub).
- **Copilot Query**:
  - Q: *"Where did the victim's money go?"*
  - A: Cites exact 4-hop trail to Binance Hot Wallet `0x28C6...` and recommends Section 91 CrPC notice.
- **Evidence Locker**:
  - Terminal transaction preserved with SHA-256 hash `d14f...`
- **Supervisor Workflow**:
  - SP Sunita Rao logs in, reviews dossier, and seals the report with approval remarks.

---

## 8. Live Blockchain Mode (Ethereum Sepolia RPC Setup)

The backend connects directly to the Ethereum Sepolia testnet to query live blocks, wallet balances, and transaction receipts.

### 8.1 Getting a Free Sepolia RPC Endpoint
You can use any of the following reliable RPC providers:

1. **Alchemy (Recommended)**:
   - Go to [alchemy.com](https://www.alchemy.com/) and create a free account.
   - Click **Create App** -> Select Network: **Ethereum** -> Sub-Network: **Sepolia**.
   - Copy the HTTPS URL: `https://eth-sepolia.g.alchemy.com/v2/<YOUR_API_KEY>`.

2. **Infura**:
   - Go to [infura.io](https://www.infura.io/) and create a free account.
   - Create a Web3 API key -> Under Endpoints, select **Sepolia**.
   - Copy the HTTPS URL: `https://sepolia.infura.io/v3/<YOUR_PROJECT_ID>`.

3. **QuickNode**:
   - Go to [quicknode.com](https://www.quicknode.com/) and register.
   - Create an endpoint for **Ethereum Sepolia**.
   - Copy the HTTPS RPC URL.

4. **Public RPCs (Zero Setup Default)**:
   - High-performance public RPCs are configured out of the box with automatic failover:
     - Primary: `https://ethereum-sepolia-rpc.publicnode.com`
     - Secondary Fallback: `https://1rpc.io/sepolia`

### 8.2 Configuring Environment Variables
Create or edit `backend/.env` (based on `.env.example`):

```env
SEPOLIA_RPC_URL=https://ethereum-sepolia-rpc.publicnode.com
ETHEREUM_RPC_URL=https://eth.llamarpc.com
DATABASE_URL=sqlite:///./data/sih26183.db
JWT_SECRET=sih26183_super_secret_forensic_investigation_jwt_key_2026
```

> **Security Note**: `backend/.env` is ignored in `.gitignore` and should never be committed to source control.

### 8.3 Starting the Backend
```bash
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

### 8.4 Manual Sepolia Connection Verification
Verify that the backend is communicating with the live Sepolia testnet using either PowerShell or cURL:

#### A. Check Sepolia Connection & Latest Block
```bash
# PowerShell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/blockchain/status" -Method Get

# cURL
curl -X GET "http://127.0.0.1:8000/blockchain/status"
```
**Expected Output**:
```json
{
  "connected": true,
  "network": "Ethereum Sepolia",
  "latest_block": 11645420
}
```

#### B. Query Real Wallet Balance on Sepolia
```bash
# PowerShell (Vitalik's address or any funded Sepolia wallet)
Invoke-RestMethod -Uri "http://127.0.0.1:8000/wallets/0xd8da6bf26964af9d7eed9e03e53415d37aa96045/balance" -Method Get

# cURL
curl -X GET "http://127.0.0.1:8000/wallets/0xd8da6bf26964af9d7eed9e03e53415d37aa96045/balance"
```
**Expected Output**:
```json
{
  "address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
  "network": "Ethereum Sepolia",
  "balance": 18456000000000000000,
  "balance_eth": 18.456
}
```

#### C. Test Invalid Wallet Address Error Handling
```bash
# PowerShell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/wallets/0xInvalidHex/balance" -Method Get

# cURL
curl -i -X GET "http://127.0.0.1:8000/wallets/0xInvalidHex/balance"
```
**Expected Output**:
`HTTP 400 Bad Request`
```json
{
  "error": "Invalid Ethereum wallet address"
}
```

#### D. Query Live Sepolia Transaction
```bash
# cURL
curl -X GET "http://127.0.0.1:8000/transactions/0x1a2b3c4d5e6f708192a1b2c3d4e5f60718293a4b5c6d7e8f9012345678abcdef"
```

#### E. Health Check
```bash
curl -X GET "http://127.0.0.1:8000/health"
```
**Expected Output**:
```json
{
  "status": "healthy",
  "app": "SIH26183 Blockchain Fraud Analytics",
  "mode": "DEMO_MODE",
  "environment": "development"
}
```

---

## 9. Phase 3: Blockchain Transaction Collection & Storage Layer

### 9.1 Purpose
Phase 3 enables automated on-chain transaction ingestion, data normalization, and persistent indexing into **Supabase PostgreSQL** with database-first caching and zero-duplicate guarantees.

### 9.2 Architecture Pipeline
```
┌─────────────────────────────────────────────────────────────┐
│                    Ethereum Sepolia Testnet                 │
│              (Chain ID: 11155111, PublicNode / Etherscan)   │
└──────────────────────────────┬──────────────────────────────┘
                               │ JSON-RPC & Explorer API
                               ▼
┌─────────────────────────────────────────────────────────────┐
│       Transaction History Provider & Web3 RPC Client        │
│       (SepoliaHistoryProvider, ResilientRPCClient)          │
└──────────────────────────────┬──────────────────────────────┘
                               │ Raw Transaction Dictionaries
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             Transaction Normalizer Layer                    │
│      (TransactionNormalizer: Wei->ETH, Types, Directions)   │
└──────────────────────────────┬──────────────────────────────┘
                               │ NormalizedTransaction Schema
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend Service                   │
│        (TransactionService: DB-First Caching, Sync Logic)   │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
               ▼                               ▼
┌──────────────────────────────┐ ┌──────────────────────────────┐
│     Supabase PostgreSQL      │ │      React UI Dashboard      │
│  (transactions & case_txs)   │ │    (Transaction Explorer)    │
│   UNIQUE(tx_hash, chain_id)  │ │   Paginated History Table    │
└──────────────────────────────┘ └──────────────────────────────┘
```

### 9.3 Database Schema (Phase 3 Migration)
Stored persistently in PostgreSQL / Supabase:
- **`transactions` Table**:
  - `id`: Integer Primary Key (Autoincrement)
  - `tx_hash`: String(128) [Indexed, Non-null]
  - `blockchain`: String(32) [Default "Ethereum", Indexed]
  - `chain_id`: Integer [Default 11155111, Indexed]
  - `block_number`: Integer [Indexed]
  - `block_hash`: String(128)
  - `transaction_index`: Integer
  - `from_address`: String(128) [Indexed, Non-null, Normalized]
  - `to_address`: String(128) [Indexed, Normalized]
  - `value_wei`: String(78) [Non-null, Full 256-bit representation]
  - `value_eth`: Float [Calculated from Wei]
  - `gas`: BigInteger
  - `gas_price_wei`: String(78)
  - `nonce`: Integer
  - `receipt_status`: String(32) ["SUCCESS" / "FAILED"]
  - `gas_used`: BigInteger
  - `block_timestamp`: DateTime [Indexed, UTC]
  - `transaction_type`: String(32) ["native_transfer" / "contract_interaction"]
  - `case_id`: String(64) [Optional Case Link]
  - `created_at` & `updated_at`: DateTime [UTC]
  - **Unique Constraint**: `UNIQUE(tx_hash, blockchain, chain_id)`
  - **Performance Indexes**: Lookups on `tx_hash`, `from_address`, `to_address`, `block_number`, `(blockchain, chain_id)`, `block_timestamp`.
- **`case_transactions` Table**:
  - `id`: Integer Primary Key
  - `case_id`: ForeignKey to `cases.case_id`
  - `transaction_id`: ForeignKey to `transactions.id`
  - `created_at`: DateTime
  - **Unique Constraint**: `UNIQUE(case_id, transaction_id)`

### 9.4 Applying Database Migrations (Alembic)
```bash
cd backend
.\venv\Scripts\Activate.ps1
alembic upgrade head
```

### 9.5 Environment Variables for Phase 3
Add to `backend/.env`:
```env
SEPOLIA_RPC_URL=https://ethereum-sepolia-rpc.publicnode.com
ETHEREUM_RPC_URL=https://eth.llamarpc.com
DATABASE_URL=sqlite:///./data/sih26183.db
# For Supabase PostgreSQL production:
# DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
JWT_SECRET=sih26183_super_secret_forensic_investigation_jwt_key_2026
TRANSACTION_HISTORY_API_URL=https://api-sepolia.etherscan.io/api
TRANSACTION_HISTORY_API_KEY=
SEPOLIA_EXPLORER_URL=https://sepolia.etherscan.io
```

### 9.6 Phase 3 API Reference
Interactive documentation available at: `http://127.0.0.1:8000/docs`

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | System health check |
| `GET` | `/database/status` | Database connection status, engine type, and table row counts |
| `GET` | `/blockchain/status` | Real-time Ethereum Sepolia RPC status & latest block |
| `GET` | `/blockchain/latest-block` | Complete block metadata of highest block on Sepolia |
| `GET` | `/wallets/{address}/validate` | Validates EVM address hex format |
| `GET` | `/wallets/{address}/balance` | Queries live balance on Sepolia testnet |
| `GET` | `/wallets/{address}/transactions` | Paginated stored transaction history (`page`, `page_size`, `direction`) |
| `POST` | `/wallets/{address}/transactions/sync` | Fetches on-chain activity, normalizes, and stores without duplicates |
| `GET` | `/transactions/{tx_hash}` | Database-first transaction detail with live fallback |
| `POST` | `/cases/{case_id}/transactions/sync` | Syncs suspect wallet for a given case and links transactions |

### 9.7 Key Blockchain Concepts for Investigators
- **Wallet Address**: A 20-byte cryptographic hash (hex string starting with `0x`) representing an account on the EVM ledger.
- **Transaction Hash**: A unique 32-byte Keccak-256 cryptographic digest identifying an on-chain transfer.
- **Block & Block Number**: Sequential batches of validated transactions cryptographically linked together.
- **RPC (Remote Procedure Call)**: Standardized JSON-RPC gateway communicating with Ethereum blockchain nodes.
- **Transaction-History Provider**: Specialized indexing service or block explorer API that indexes transactions by account.
- **PostgreSQL Cache & Storage**: Local indexed store enabling instant search, pagination, and offline evidence preservation without repetitive external RPC costs.

---

## 10. Judicial & Forensic Compliance Disclaimer
This platform is strictly an analytical and evidence-gathering instrument. Behavioral patterns and risk scores represent system and AI inferences intended to guide investigation priorities for human law enforcement officers and do not constitute legal proof of guilt. All conclusions must be verified using underlying on-chain transactions and validated exchange records.

