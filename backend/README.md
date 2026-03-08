# Backend — Phishing Detection System

The backend is a Python-based SMTP server that classifies incoming emails using a trained ML model, persists results to SQLite, and optionally sends scan-result replies back to users.

---

## Directory Structure

```
backend/
├── requirements.txt          # Python dependencies
├── app/                      # Main application package
│   ├── smtp_server.py        # Entry point — SMTP server & processing pipeline
│   ├── phishing_detector.py  # ML model wrapper & email preprocessor
│   ├── database.py           # DatabaseManager (SQLAlchemy CRUD helpers)
│   ├── models.py             # SQLAlchemy ORM models (User, EmailEvent, Prediction, TrustedDomain)
│   ├── init_db.py            # One-time DB initialisation & smoke-test script
│   └── utils/
│       └── clean_and_merge.py  # Dataset cleaning utility (ML training use)
└── ml/                       # Machine learning assets
    ├── models/
    │   ├── model_a/          # Baseline model (Model A)
    │   └── model_b/          # Active model — loaded by default
    │       ├── phishing_model_b.joblib
    │       ├── tfidf_vectorizer_b.joblib
    │       └── v1/           # Previous Model B checkpoint
    ├── notebooks/            # Jupyter training notebooks
    └── data/
        ├── raw/              # Source CSV datasets
        └── processed/        # Merged/cleaned dataset
```

---

## Setup

### 1. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

Requires **Python 3.10+**.

### 2. Initialise the database

Run once to create `phishing_detector.db` and verify the DB layer:

```bash
cd backend/app
python init_db.py
```

The SQLite file is created in whichever directory you run the command from.

### 3. Register users

Use `DatabaseManager` directly (see `init_db.py` for examples) or expose a registration endpoint in your API layer.

### 4. Start the SMTP server

```bash
cd backend/app
python smtp_server.py --host localhost --port 1025
```

Full options:

```
--host          Bind address              (default: localhost)
--port          Listen port               (default: 1025)
--model-dir     Override model directory  (default: ../ml/models/model_b)
--whitelist     Add extra trusted domains
--no-whitelist  Disable built-in whitelist
--reply         Enable auto-reply emails
--reply-host    Outbound relay host       (default: localhost)
--reply-port    Outbound relay port       (default: 25)
--reply-from    Sender address for replies
```

---

## API Reference

Full API documentation is in [`../docs/BACKEND_API.md`](../docs/BACKEND_API.md).

Key classes:

| Class / Module         | File                    | Purpose                                  |
|------------------------|-------------------------|------------------------------------------|
| `PhishingDetector`     | `app/phishing_detector.py` | Load model, preprocess & classify email |
| `DatabaseManager`      | `app/database.py`       | Create/query users, events, predictions  |
| ORM Models             | `app/models.py`         | SQLAlchemy table definitions             |
| SMTP Entry Point       | `app/smtp_server.py`    | Wires everything together, exposes SMTP  |

---

## ML Models

| Model     | Location                          | Notes                          |
|-----------|-----------------------------------|--------------------------------|
| Model B   | `ml/models/model_b/`              | **Default / active model**     |
| Model B v1| `ml/models/model_b/v1/`           | Previous checkpoint            |
| Model A   | `ml/models/model_a/`              | Baseline (for comparison)      |

Training notebooks are in `ml/notebooks/`.

---

## Running with a Frontend API Layer

When adding a REST/GraphQL API for the frontend, create a new `app/api.py` (or a `app/routes/` package) that imports from `database.py` and `phishing_detector.py`. The SMTP server and the API layer share the same `DatabaseManager` instance.

Suggested stack: **FastAPI** + **Uvicorn** — install separately alongside this `requirements.txt`.
