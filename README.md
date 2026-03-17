# Phishing Email Detection and Reporting System

A full-stack application that scans incoming emails for phishing using a machine-learning model and presents results in a web dashboard.

## Features

- **React Dashboard** — Per-user scan history, risk charts, summary cards, and domain management
- **Registered-User Pipeline** — Only processes emails from users registered on the platform
- **ML Classification** — TF-IDF (unigram–trigram) + LinearSVC with probability calibration
- **Domain Whitelisting** — Global built-in whitelist plus per-user trusted domains
- **Email Alerts Toggle** — Users can enable/disable scan-result reply emails from the dashboard
- **SMTP Scanner** — Receives emails on port 1025 via aiosmtpd; evaluates the actual sending domain even when forwarded through Gmail
- **SQLite Database** — Persists users, scan events, predictions, and trusted domains via SQLAlchemy

## Requirements

- Python 3.10+
- Node.js 18+
- Pre-trained model files (included in repo under `backend/ml/models/model_b/`)

## Installation

```bash
git clone https://github.com/Fortcode-LK/Phishing-Email-Detection-and-Reporting-System.git
cd Phishing-Email-Detection-and-Reporting-System

# Backend
pip install -r backend/requirements.txt

# Frontend
cd frontend && npm install
```

## Running the System

Start all three components in separate terminals:

**Terminal 1 — Backend API (port 8000):**
```bash
cd backend/app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Frontend (port 5173):**
```bash
cd frontend
npm run dev
```

**Terminal 3 — SMTP Scanner (port 1025):**
```bash
cd backend/app
python smtp_server.py
```

Open `http://localhost:5173`, register an account, then scan emails using the Gmail forwarding tool or any SMTP client.

## Scanning Emails

### Gmail Forwarding Tool

```bash
cd tools
python gmail_forwarder.py
```

Requires IMAP enabled in Gmail settings and a **Gmail App Password** (not your regular password). The envelope sender must match your registered account email. See [USAGE.md](USAGE.md) for full setup instructions.

### SMTP Client

```python
import smtplib
from email.message import EmailMessage

msg = EmailMessage()
msg['From'] = 'Sender <sender@example.com>'
msg['To'] = 'you@registered.email'
msg['Subject'] = 'Subject to scan'
msg.set_content('Email body here')

with smtplib.SMTP('localhost', 1025) as s:
    s.sendmail('you@registered.email', ['you@registered.email'], msg.as_bytes())
```

## SMTP Scanner CLI Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | `localhost` | SMTP bind host |
| `--port` | `1025` | SMTP bind port |
| `--model-dir` | auto | Path to model directory |
| `--whitelist DOMAIN …` | — | Extra domains to whitelist |
| `--no-whitelist` | off | Disable built-in whitelist |
| `--reply` | off | Enable scan-result auto-reply emails |
| `--reply-host` | `localhost` | Outbound SMTP relay host |
| `--reply-port` | `25` | Outbound SMTP relay port |
| `--reply-from` | `phishing-scanner@localhost` | Reply From address |

## SMTP Response Codes

| Code | Meaning |
|------|---------|
| `250 OK` | Email classified and logged |
| `550 Rejected - sender not registered` | Envelope sender not in database |
| `550 Rejected - message could not be parsed` | Malformed email |
| `421 Temp fail` | Internal server error |

## Project Structure

```
phishing-project/
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py                 # FastAPI application
│   │   ├── smtp_server.py          # SMTP scanner & ML pipeline
│   │   ├── phishing_detector.py    # ML wrapper & email preprocessor
│   │   ├── database.py             # SQLAlchemy DatabaseManager
│   │   ├── models.py               # ORM models
│   │   ├── schemas.py              # Pydantic schemas
│   │   ├── auth.py                 # JWT authentication
│   │   └── init_db.py              # DB initialisation
│   └── ml/
│       ├── models/model_b/         # Active ML model (TF-IDF + LinearSVC)
│       └── data/                   # Training datasets
├── frontend/
│   └── src/
│       ├── routes/                 # Page components
│       ├── components/             # Reusable UI components
│       └── hooks/                  # React Query data hooks
├── tools/
│   └── gmail_forwarder.py          # Gmail IMAP → local SMTP utility
└── docs/
    └── BACKEND_API.md              # API reference
```

## Documentation

| File | Contents |
|------|----------|
| [USAGE.md](USAGE.md) | End-to-end setup and usage guide |
| [GMAIL_TESTING.md](GMAIL_TESTING.md) | Gmail forwarding setup |
| [docs/BACKEND_API.md](docs/BACKEND_API.md) | Backend API reference |

## License

See repository license.
