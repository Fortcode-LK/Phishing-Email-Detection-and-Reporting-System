# Phishing Detection System — User Guide

## What This System Does

The Phishing Email Detection and Reporting System scans incoming emails using a machine-learning model and reports results through a web dashboard. It has three components running simultaneously:

| Component | Port | Purpose |
|-----------|------|---------|
| FastAPI backend | 8000 | REST API, user auth, scan history |
| Vite frontend | 5173 | Dashboard UI |
| SMTP scanner | 1025 | Receives emails, runs ML model, logs results |

---

## Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- A registered account on the system (register at `http://localhost:5173`)

Install Python dependencies:
```bash
pip install -r backend/requirements.txt
```

Install frontend dependencies:
```bash
cd frontend
npm install
```

---

## Starting the System (3 terminals)

**Terminal 1 — Backend API:**
```bash
cd backend/app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

**Terminal 3 — SMTP Scanner:**
```bash
cd backend/app
python smtp_server.py
```

To also receive a scan-result reply email after each scan:
```bash
python smtp_server.py --reply --reply-host <your-smtp-relay> --reply-port 587
```

Open `http://localhost:5173` in your browser once all three are running.

---

## Scanning Emails

### Option A — Gmail Forwarding Tool (recommended)

The included `tools/gmail_forwarder.py` script fetches emails from your Gmail inbox via IMAP and forwards them to the local SMTP scanner automatically.

**Requirements:**
- Gmail IMAP must be enabled: Gmail Settings → See all settings → Forwarding and POP/IMAP → Enable IMAP
- You must use a **Gmail App Password**, not your regular password. Create one at `https://myaccount.google.com/apppasswords` (requires 2-Step Verification to be enabled)
- The email address you use must be registered as a user on the system

**Run the tool:**
```bash
cd tools
python gmail_forwarder.py
```

Select option `1` (IMAP fetch), enter your Gmail address and App Password, then choose how many emails to fetch.

### Option B — Manual paste

Select option `2` in the forwarder to paste raw email content directly.

### Option C — Any SMTP client

Send an email to `localhost:1025` with the `MAIL FROM` envelope address set to your registered email:
```python
import smtplib
from email.message import EmailMessage

msg = EmailMessage()
msg['From'] = 'Sender <sender@example.com>'
msg['To'] = 'you@yourregistered.email'
msg['Subject'] = 'Subject to scan'
msg.set_content('Body text here')

with smtplib.SMTP('localhost', 1025) as s:
    s.sendmail('you@yourregistered.email', ['you@yourregistered.email'], msg.as_bytes())
```

---

## Reading the Results

After each email is processed the SMTP scanner prints a one-line result:

```
PROCESSED user_id=8 | PHISHING 85.31% [HIGH] via model_prediction
TRUSTED  user_id=8 | no-reply@accounts.google.com -> skipping model
```

**Risk levels:**

| Level | Phishing probability |
|-------|----------------------|
| LOW | 0 – 40% |
| MEDIUM | 40 – 70% |
| HIGH | 70 – 100% |

Results are also saved to the database and appear in the dashboard at `http://localhost:5173`.

---

## Dashboard Features

- **Summary cards** — total scans, phishing count, legitimate count
- **Scan history table** — per-email results with sender domain, risk level, and timestamp
- **Charts** — scan trend over time, risk distribution donut, top sender domains
- **Trusted domains** — add domains you trust so they always skip the model
- **Email alerts toggle** — enable/disable scan-result reply emails per account

---

## Domain Whitelisting

Emails from globally trusted domains (Google, GitHub, Microsoft, PayPal, etc.) are automatically marked legitimate without running the model. You can add your own trusted domains per account in the dashboard under **Trusted Domains**.

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `550 Rejected - sender not registered` | Envelope sender not in DB | Ensure `MAIL FROM` matches your registered email |
| `421 Temp fail` | SMTP handler crashed | Check the scanner terminal for the traceback |
| `IMAP EOF` during Gmail fetch | Gmail dropped the connection on a large email | The forwarder auto-reconnects and retries; just re-run |
| All emails show `via trusted_domain` | Sender domain is on the global whitelist | Expected — no model needed for known-safe senders |
| Reply emails not sent | No SMTP relay on the configured reply port | Use `--reply-host` / `--reply-port` pointing to a real relay, or omit `--reply` |
  Sender: test.user@example.com
  Label: PHISHING
  Probability: 94.23%
============================================================
```

## Forwarding Emails to the Detector

### Manual Forward
1. Start the detector server
2. Use any email client to forward suspicious emails to localhost:1025
3. View classification results in the terminal

### Programmatic Integration
```python
import smtplib
from email.mime.text import MIMEText

msg = MIMEText("Email body here")
msg['Subject'] = 'Fwd: Suspicious Email'
msg['From'] = 'you@example.com'
msg['To'] = 'detector@localhost'

with smtplib.SMTP('localhost', 1025) as server:
    server.send_message(msg)
```

## Model Files

The system uses pre-trained models from:
- `backend/ml/models/model_b/phishing_model_b.joblib`
- `backend/ml/models/model_b/tfidf_vectorizer_b.joblib`

These must exist for the system to work.

## Troubleshooting

**Port already in use:**
```bash
python phishing_detector.py --port 1026
```

**Model not found:**
- Verify files exist in `backend/ml/models/model_b/`
- Or specify custom path: `--model-dir /path/to/models`

**Cannot send test emails:**
- Ensure detector server is running first
- Check firewall settings for localhost connections

## Security Notes

- This server is for **LOCAL TESTING ONLY**
- Do not expose to external networks
- Runs on localhost by default for security
- No authentication implemented (testing purposes)
