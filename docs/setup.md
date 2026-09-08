# Setup Guide: SIH26183 Investigation Platform

## Prerequisites
- Python 3.12+ installed
- Node.js v20+ and npm installed
- Git

---

## 1. Backend Setup

```bash
# Navigate to backend folder
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Linux / macOS:
# source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Start backend server
uvicorn app.main:app --reload --port 8000
```

The backend server will run at `http://127.0.0.1:8000`.
OpenAPI documentation is available at `http://127.0.0.1:8000/docs`.

---

## 2. Frontend Setup

```bash
# Navigate to frontend folder
cd frontend

# Install npm dependencies
npm install

# Start development server
npm run dev
```

The frontend dashboard will run at `http://127.0.0.1:5173`.

---

## 3. Running Automated Tests

```bash
cd backend
.\venv\Scripts\pytest -v
```

All 12 unit and integration tests covering address validation, graph construction, multi-hop path finding, risk heuristics, evidence integrity, and end-to-end demo flow will execute.
