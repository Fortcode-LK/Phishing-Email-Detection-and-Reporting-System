# Phishing Email Detection System

An SMTP-based phishing detection system that receives emails, preprocesses them, classifies them with a trained ML model, logs results to a database, and optionally sends scan-result replies back to users.

## Features

- **SMTP Server** — Receives emails on a configurable port via aiosmtpd
- **Registered-User Pipeline** — Only processes emails from users registered in the database; rejects unknown senders with `550`
- **Email Preprocessing** — HTML stripping, Unicode normalisation, forwarded-email extraction, CSS/signature removal
- **ML Classification** — TF-IDF (unigram–trigram) + LinearSVC with probability calibration
- **Domain Whitelisting** — Global built-in whitelist (Google, GitHub, Reddit, etc.) plus per-user trusted domains stored in the DB
- **SQLite Database** — Persists users, email events, predictions, and trusted domains via SQLAlchemy
- **Auto-Reply** — Optionally sends a scan-result email back to the forwarding address (enable with `--reply`)
- **Forward-Aware Trust** — Detects forwarded emails and evaluates the _original_ sender's domain, not the forwarding address

## Requirements

- Python 3.10+
- See [requirements.txt](requirements.txt) for all dependencies

```
aiosmtpd>=1.4.4
joblib>=1.3.0
scikit-learn~=1.6.1
beautifulsoup4>=4.12.0
lxml>=4.9.0
sqlalchemy==2.0.25
```

## Installation

```bash
git clone https://github.com/Fortcode-LK/Phishing-Email-Detection-and-Reporting-System.git
cd Phishing-Email-Detection-and-Reporting-System
pip install -r requirements.txt
```

## Setup

### 1. Verify model files exist

The system requires pre-trained model files:

```
models/model b/trainning2/phishing_model_b.joblib
models/model b/trainning2/tfidf_vectorizer_b.joblib
```

### 2. Initialise the database

Run the init script once to create the SQLite database and verify the DB layer:

```bash
cd src
python init_db.py
```

This creates `phishing_detector.db` in the working directory.

### 3. Register users

Users must be registered in the database before the server will accept their emails. Use `DatabaseManager` directly or integrate with your user-registration flow:

```python
import hashlib
from database import DatabaseManager

db = DatabaseManager()
db.create_user(
    email_hash=hashlib.sha256("user@example.com".lower().encode()).hexdigest(),
    password_hash=hashlib.sha256("password".encode()).hexdigest(),
    first_name="Alice",
    last_name="Smith",
    mobile_number="+15550001234",
    address="123 Main St",
)
```

## Running the Server

### Option A — Full pipeline (SMTP + DB + auto-reply)

```bash
cd src
python smtp_server.py
```

With auto-reply enabled (sends scan results back to the user):

```bash
python smtp_server.py --reply --reply-host localhost --reply-port 25
```

**All CLI flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | `localhost` | SMTP bind host |
| `--port` | `1025` | SMTP bind port |
| `--model-dir` | auto | Path to model directory |
| `--whitelist DOMAIN …` | — | Extra domains to whitelist |
| `--no-whitelist` | off | Disable built-in whitelist |
| `--reply` | off | Enable scan-result auto-reply |
| `--reply-host` | `localhost` | Outbound SMTP relay host |
| `--reply-port` | `25` | Outbound SMTP relay port |
| `--reply-from` | `phishing-scanner@localhost` | Reply From address |

### Option B — Standalone detector (no DB)

```bash
cd src
python phishing_detector.py --port 1025
```

This runs a bare SMTP listener that classifies emails and prints results to stdout, without database logging or user registration checks.

## Sending Emails to the Server

```python
import smtplib
from email.mime.text import MIMEText

msg = MIMEText("Click here to verify your account: http://suspicious-link.example")
msg["Subject"] = "Urgent: Account Verification Required"
msg["From"] = "registered-user@example.com"
msg["To"] = "detector@localhost"

with smtplib.SMTP("localhost", 1025) as s:
    s.send_message(msg)
```

## Gmail Forwarding

See [GMAIL_TESTING.md](GMAIL_TESTING.md) for instructions on forwarding real Gmail emails to the detector using `tools/gmail_forwarder.py`.

## SMTP Response Codes

| Code | Meaning |
|------|---------|
| `250 OK - processed successfully` | Email classified and logged |
| `550 Rejected - sender not registered` | Sender is not in the database |
| `550 Rejected - message could not be parsed` | Malformed email |
| `421 Temp fail - try again later` | Internal server error |

## Project Structure

```
phishing-project/
├── src/
│   ├── smtp_server.py          # DB-integrated SMTP router (production)
│   ├── phishing_detector.py    # Standalone SMTP detector (no DB)
│   ├── database.py             # SQLAlchemy DatabaseManager
│   ├── models.py               # ORM models (User, EmailEvent, Prediction, TrustedDomain)
│   └── init_db.py              # DB initialisation and smoke-test script
├── tools/
│   └── gmail_forwarder.py      # Gmail → local SMTP forwarding utility
├── models/
│   └── model b/trainning2/     # Pre-trained ML model files
├── data/
│   └── processed/emails_merged.csv
├── requirements.txt
└── docs/
    ├── BACKEND_API.md          # Full backend developer reference
    └── notes/
```

## Documentation

| File | Contents |
|------|----------|
| [QUICKSTART.md](QUICKSTART.md) | Fast installation and first run |
| [USAGE.md](USAGE.md) | Detailed configuration and usage |
| [GMAIL_TESTING.md](GMAIL_TESTING.md) | Testing with real Gmail emails |
| [docs/BACKEND_API.md](docs/BACKEND_API.md) | Backend API reference for developers |

## License

See repository license.
