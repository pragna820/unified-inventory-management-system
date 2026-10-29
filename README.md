# Unified Inventory Management System

Tracks inventory across stores, warehouses and online channels, with an immutable movement ledger, ATP, reservations, orders, transfers, replenishment, and anomaly detection. **All data is synthetic.**

## Stage status

| Stage | Scope | Status |
|---|---|---|
| 1 | Architecture, folders, data dictionary, schema, business rules | ✅ done (13 tests pass) |
| 2 | Alembic + PostgreSQL, master data, starter dataset, ledger | next |
| 3 | ATP, reservations, orders, transfers, replenishment | |
| 4 | API + backend tests | |
| 5 | React dashboard | |
| 6 | Anomalies, ground truth, metrics | |
| 7 | Exports, reproducibility, full-scale run | |

## Architecture

```
React (Vite) ──HTTP/JSON──► FastAPI routers ──► service layer (business rules) ──► SQLAlchemy ──► PostgreSQL
                                                     ▲
                              data generator + validators call the same services
```

* **Routers** only validate input (Pydantic) and call services.
* **Services** hold every business rule (ATP, reservations, allocation…). The generator uses them, so generated data obeys the same rules as the API.
* **Ledger first:** balances are derived from movements and can always be re-checked.

## Folder structure

```
unified-inventory/
├── backend/
│   ├── app/
│   │   ├── core/        config, db session, ID formatters
│   │   ├── models/      enums + SQLAlchemy tables
│   │   ├── services/    business rules (Stage 3)
│   │   ├── api/         FastAPI routers (Stage 4)
│   │   ├── data/        generator (Stage 2)
│   │   └── tools/       data-dictionary generator
│   ├── alembic/         migrations (Stage 2)
│   ├── tests/
│   └── requirements.txt
├── frontend/            React + Vite (Stage 5)
├── data/                starter/, full/, exports/
├── docs/                schema, rules, data dictionary, reports
├── docker-compose.yml   optional PostgreSQL
└── .env.example
```

## Setup (Windows PowerShell, VS Code terminal)

Prerequisites: Python 3.11+, Git, and (from Stage 2) PostgreSQL 16 or Docker Desktop, plus Node 20+ (Stage 5).

```powershell
cd unified-inventory
git init
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
# If activation is blocked:  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
python -m pip install --upgrade pip
pip install -r requirements.txt
copy ..\.env.example .env     # then edit .env: put your own DB password
```

### Run the Stage 1 tests

```powershell
cd backend
python -m pytest -v
```
Expected: `13 passed`.

### Regenerate the data dictionary

```powershell
python -m app.tools.gen_data_dictionary
```
Writes `docs/data_dictionary.md` from the models.

## Docs
[schema](docs/schema.md) · [business rules](docs/business_rules.md) · [data dictionary](docs/data_dictionary.md) · [validation report](docs/validation_report.md) · [source manifest](docs/source_manifest.md)
