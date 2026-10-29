# Unified Inventory Management System

## Overview

The Unified Inventory Management System is a web-based application designed to organize product and inventory information. It uses a React frontend, a FastAPI backend, and PostgreSQL for data storage.

The project is being developed to support inventory management across multiple stores, warehouses, and online sales channels.

## Key Features

- Product information management
- SKU and product variant structure
- Inventory movement API
- PostgreSQL database integration
- Database schema management using SQLAlchemy and Alembic
- REST API documentation through Swagger UI
- React-based user interface

**Project status:** The application is under development. Product creation and the backend health endpoint have been tested. Some SKU and inventory movement operations require further debugging and validation.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React, Vite, JavaScript |
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Testing | pytest |

## Project Structure

```text
unified-inventory-management-system/
├── backend/
│   ├── app/
│   ├── migrations/
│   ├── tests/
│   ├── requirements.txt
│   └── alembic.ini
├── frontend/
├── docs/
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

## Prerequisites

Install the following tools:

- Python 3
- Node.js and npm
- PostgreSQL, configured for this project
- Git

## Setup and Run

### 1. Clone the repository

```bash
git clone https://github.com/pragna820/unified-inventory-management-system.git
cd unified-inventory-management-system
```

### 2. Configure the environment

Review `.env.example` and configure the environment variables required by the application. Use your own local database credentials.

Never commit real passwords, API keys, or secret environment files.

### 3. Set up the backend

Open a terminal in the project directory:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Configure the PostgreSQL database and connection settings before running migrations:

```powershell
alembic upgrade head
```

Start the API server:

```powershell
python -m uvicorn app.main:app --reload
```

The backend should be available at `http://127.0.0.1:8000`.

API documentation: `http://127.0.0.1:8000/docs`

Health endpoint: `http://127.0.0.1:8000/health`

### 4. Set up the frontend

Open a second terminal from the repository root:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL shown in the terminal, usually `http://localhost:5173`.

## Tests

The backend includes tests under `backend/tests/`. Run them from the `backend` directory:

```powershell
python -m pytest -v
```

Review the test results to confirm the current status in your environment.

## Documentation

Additional project documentation is available in the `docs/` directory, including the data dictionary, schema, business rules, source manifest, and validation report.

## Security

- Keep local credentials in environment files that are excluded from Git.
- Use `.env.example` for placeholder configuration only.
- Do not upload passwords, private keys, or other secrets to the public repository.

## Future Improvements

- Complete and validate SKU operations
- Improve inventory movement handling
- Expand automated API and integration tests
- Continue developing inventory workflows and dashboard functionality

## Author

Pragna Vuyyuru
