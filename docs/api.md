# REST API Reference: SIH26183 Blockchain Analytics

Base URL: `http://127.0.0.1:8000/api`

## Authentication (`/auth`)
- `POST /auth/register` - Register officer or victim account
- `POST /auth/login` - Authenticate and retrieve Bearer JWT
- `GET /auth/me` - Get current user profile and role
- `POST /auth/seed-users` - Populate default evaluation accounts (Investigator, Supervisor, Admin, Victim)

## Case Management (`/cases`)
- `POST /cases` - Create a new fraud investigation case
- `GET /cases` - List all cases accessible to current user role
- `GET /cases/{case_id}` - Get full case details
- `PATCH /cases/{case_id}` - Update case status or priority
- `POST /cases/seed-demo` - Initialize official SIH Hackathon demonstration scenario
- `GET /cases/{case_id}/notes` - List investigator field notes
- `POST /cases/{case_id}/notes` - Record a new field note

## Wallet Forensics (`/wallets`)
- `POST /wallets/analyze` - Perform multi-hop graph analysis and risk evaluation on an address
- `GET /wallets/{address}/transactions` - Retrieve indexed transactions for a wallet

## Graph & Money Trail Analysis (`/analysis`)
- `GET /analysis/graph/{case_id}?hops=3&suspicious_only=false` - Retrieve interactive node-link graph payload
- `GET /analysis/trail/{case_id}?max_hops=5` - Extract step-by-step money trail from victim to VASP
- `GET /analysis/patterns/{case_id}` - Get all detected heuristic patterns and risk breakdown

## Cryptographic Evidence Locker (`/evidence`)
- `POST /evidence` - Preserve transaction flow with SHA-256 integrity hash
- `GET /evidence/{case_id}` - Retrieve all preserved evidence for a case

## Grounded Investigation Copilot (`/copilot`)
- `POST /copilot/query` - Context-grounded Q&A over verified case transactions and risk findings

## Wallet Watchlist & Surveillance (`/monitoring`)
- `POST /monitoring` - Place wallet on surveillance watchlist
- `GET /monitoring/case/{case_id}` - Get monitored addresses for a case
- `GET /monitoring/alerts` - List triggered high-risk activity alerts
- `POST /monitoring/simulate-alert/{monitoring_id}` - Trigger simulated high-risk inflow alert

## Forensic Reports & Review (`/reports`)
- `POST /reports/generate` - Generate structured forensic dossier
- `GET /reports/case/{case_id}` - List reports for a case
- `GET /reports/{report_id}` - Get report by ID
- `PATCH /reports/{report_id}/review` - Supervisor approval or rejection sign-off

## Address Labels & Intelligence (`/labels`)
- `GET /labels` - Query recognized VASP and exchange directory
- `POST /labels` - Register or update entity label
