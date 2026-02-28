# Backend API Documentation

> **Audience:** Backend developers integrating with or extending the phishing detection system.  
> **Last updated:** 2026-02-28  
> **Repo:** `src/smtp_server.py` · `src/database.py` · `src/models.py` · `src/phishing_detector.py`

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [SMTP Server](#2-smtp-server)
   - [Starting the Server](#21-starting-the-server)
   - [Processing Pipeline](#22-processing-pipeline)
   - [SMTP Response Codes](#23-smtp-response-codes)
   - [Auto-Reply System](#24-auto-reply-system)
   - [Global Whitelist](#25-global-whitelist)
3. [Database Layer — `DatabaseManager`](#3-database-layer--databasemanager)
   - [Initialisation](#31-initialisation)
   - [User Management](#32-user-management)
   - [Email Events](#33-email-events)
   - [Predictions](#34-predictions)
   - [Trusted Domains](#35-trusted-domains)
   - [Query Methods](#36-query-methods)
4. [Database Schema](#4-database-schema)
5. [ML Detector — `PhishingDetector`](#5-ml-detector--phishingdetector)
   - [Initialisation](#51-initialisation)
   - [`classify_email(subject, body)`](#52-classify_emailsubject-body)
   - [`preprocess_email(raw_email)`](#53-preprocess_emailraw_email)
   - [`is_whitelisted(email_address)`](#54-is_whitelistedemail_address)
6. [Internal Helper Functions](#6-internal-helper-functions)
7. [Integration Guide](#7-integration-guide)
   - [Registering a User](#71-registering-a-user)
   - [Per-User Trusted Domains](#72-per-user-trusted-domains)
   - [Reading Scan History](#73-reading-scan-history)
   - [Programmatic Embedding](#74-programmatic-embedding)
8. [Error Reference](#8-error-reference)
9. [End-to-End Test](#9-end-to-end-test)

---

## 1. Architecture Overview

The system is designed for the **auto-forwarding** model: users configure their email provider (Gmail, Outlook, etc.) to automatically forward all incoming mail to this server's SMTP port. The server then classifies each email and sends the scan result back to the user's inbox.

```
User's inbox (Gmail / Outlook)
        │  auto-forward
        ▼
┌───────────────────────────────────┐
│   SMTP Server  (port 1025)        │
│   smtp_server.py                  │
│                                   │
│  envelope sender = user's address │
│  original sender = parsed from    │
│                    forwarded body │
│                                   │
│   1. Validate registered user     │
│   2. Preprocess email             │
│   3. Log EmailEvent to DB         │
│   4. Trusted-domain check         │
│   5. Run ML model (if not trusted)│
│   6. Log Prediction to DB         │
│   7. Send auto-reply (optional)   │
└───────────────────────────────────┘
        │  scan result reply
        ▼
User's inbox
```

**Key design rule:** The SMTP **envelope sender** (`mail from:`) is always the user's own forwarding address and is only used to look up the `User` record. All trust/whitelist decisions are made against the **original sender** extracted from the forwarded email body.

---

## 2. SMTP Server

**File:** `src/smtp_server.py`  
**Entry point:** `python src/smtp_server.py [options]`

### 2.1 Starting the Server

```bash
python src/smtp_server.py \
  --host     localhost \        # bind address          (default: localhost)
  --port     1025 \             # listen port           (default: 1025)
  --model-dir path/to/models \  # override model path   (default: auto-detected)
  --whitelist corp.com org.io \ # extra whitelist domains (additive)
  --no-whitelist \              # disable built-in whitelist entirely
  --reply \                     # enable auto-reply emails
  --reply-host smtp.relay.com \ # outbound relay host   (default: localhost)
  --reply-port 587 \            # outbound relay port   (default: 25)
  --reply-from scanner@org.com  # reply From address
```

The server blocks on `asyncio.get_event_loop().run_forever()`. Stop it with `Ctrl+C`.

---

### 2.2 Processing Pipeline

Every inbound SMTP `DATA` command triggers `handle_smtp_email()` which executes the following steps in order:

| Step | Action | On failure |
|------|--------|-----------|
| **1** | Look up `User` by `SHA-256(sender_email)` | Return `550`, discard |
| **2** | Preprocess raw email bytes → subject / body / original_sender | Return `550`, discard |
| **3** | Write `EmailEvent` row to DB (true origin domain, is_forwarded flag) | Exception propagates → `421` |
| **4** | Check trusted-domain list (global whitelist first, then per-user DB) | — |
| **5** | If not trusted: run `PhishingDetector.classify_email()` | Exception propagates → `421` |
| **6** | Write `Prediction` row to DB | Exception propagates → `421` |
| **7** | Send auto-reply to user's inbox (best-effort, never raises) | Logged as `REPLY FAILED`, pipeline continues |

**Forwarded-email address resolution:**

```python
# True origin = original_sender extracted from forward headers in body.
# Fall back to envelope sender only for direct (non-forwarded) delivery.
check_address = original_sender if original_sender else sender_email
check_domain  = get_sender_domain(check_address)
```

Trust checks and `EmailEvent.senderDomain` always use `check_domain`, never the forwarding user's domain.

---

### 2.3 SMTP Response Codes

| Code | Text | Condition |
|------|------|-----------|
| `250` | `OK - processed successfully` | Email fully processed and logged |
| `550` | `Rejected - sender not registered` | `envelope.mail_from` not in the `User` table |
| `550` | `Rejected - message could not be parsed` | `preprocess_email()` returned `None` |
| `421` | `Temp fail - try again later` | Unhandled exception in the handler (DB error, model error, etc.) |

`421` signals the sending MTA to retry — the connection is dropped immediately. `550` is permanent rejection.

---

### 2.4 Auto-Reply System

Implemented in `send_scan_reply()`. Disabled by default; enabled with `--reply`.

**Reply is sent to:** `sender_email` (the user's forwarding address — their real inbox), **not** the original/attacker address.

**Reply subject format:**
```
[Phishing Scan] ⚠ PHISHING – <original subject>
[Phishing Scan] ✔ Safe – <original subject>
```

**Reply body fields:**

| Field | Description |
|-------|-------------|
| `Scanned email` | Original subject line |
| `Verdict` | `⚠ PHISHING detected (N% confidence)` or `✔ Safe (N% confidence)` |
| `Risk level` | `HIGH` / `MEDIUM` / `LOW` |
| `Checked via` | `model_prediction` or `trusted_domain` |

**Failure behaviour:** `send_scan_reply()` catches all exceptions internally and prints `REPLY FAILED to <addr>: <reason>`. The pipeline always returns `250` regardless of reply success or failure.

**Outbound relay:** Uses `smtplib.SMTP` (stdlib, no extra dependencies). Configure with `--reply-host`, `--reply-port`, `--reply-from`.

---

### 2.5 Global Whitelist

Built-in domains that bypass the ML model for all users (evaluated against `check_address`, i.e. the true email origin):

```
google.com      accounts.google.com     gmail.com
microsoft.com   apple.com               amazon.com
github.com      linkedin.com            twitter.com
facebook.com    instagram.com           reddit.com
redditmail.com  paypal.com
```

Override behaviour:
- `--whitelist extra.com` — adds `extra.com` to the built-in list
- `--no-whitelist` — disables the built-in list entirely (per-user DB trusted domains still apply)

Risk level thresholds (model path only):

| `phishing_probability` | `risk_level` |
|------------------------|--------------|
| ≥ 0.85 | `HIGH` |
| ≥ 0.55 | `MEDIUM` |
| < 0.55 | `LOW` |

---

## 3. Database Layer — `DatabaseManager`

**File:** `src/database.py`  
**Engine:** SQLite via SQLAlchemy 2.x  
**Default DB file:** `phishing_detector.db` (relative to CWD)  
**Override:** Set `database.DATABASE_URL` before instantiation, or set the `DATABASE_URL` env variable.

### 3.1 Initialisation

```python
from database import DatabaseManager

db = DatabaseManager()  # creates tables if they don't exist
```

`DatabaseManager.__init__()` calls `Base.metadata.create_all()` — safe to call on an existing DB (no-op if tables already exist).

All methods use an internal `_session_scope()` context manager that commits on success and rolls back on any exception. Returned ORM objects have `expire_on_commit=False` so they remain usable after the session closes.

---

### 3.2 User Management

#### `create_user(email_hash, password_hash, first_name, last_name, mobile_number, address)`

Creates a new `User` record.

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `email_hash` | `str` | ✅ | `SHA-256(email.strip().lower())` — plain email is **never** stored |
| `password_hash` | `str` | ✅ | Pre-hashed by caller |
| `first_name` | `str` | ❌ | |
| `last_name` | `str` | ❌ | |
| `mobile_number` | `str` | ❌ | Must be unique if provided |
| `address` | `str` | ❌ | |

**Returns:** `User` ORM object  
**Raises:** `ValueError("User with this email hash already exists")` on duplicate

```python
import hashlib

def make_hash(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode()).hexdigest()

user = db.create_user(
    email_hash    = make_hash("alice@example.com"),
    password_hash = make_hash("s3cret"),
    first_name    = "Alice",
    last_name     = "Smith",
)
print(user.id)   # auto-assigned integer PK
```

---

#### `get_user_by_email_hash(email_hash)`

Looks up a user by pre-computed hash.

**Returns:** `User` or `None`

```python
user = db.get_user_by_email_hash(make_hash("alice@example.com"))
if user is None:
    # sender not registered → reject
```

---

### 3.3 Email Events

#### `log_email_event(user_id, sender_domain, is_forwarded, message_id_hash)`

Writes one record per inbound email.

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `user_id` | `int` | ✅ | FK → `User.id` |
| `sender_domain` | `str` | ✅ | **True origin domain** (not the forwarding user's domain) |
| `is_forwarded` | `bool` | ❌ | `True` if `original_sender` was detected in headers |
| `message_id_hash` | `str \| None` | ❌ | `SHA-256(Message-Id header)` for dedup |

**Returns:** `EmailEvent` ORM object  
`EmailEvent.id` is needed to call `log_prediction()`.

```python
event = db.log_email_event(
    user_id        = user.id,
    sender_domain  = "attacker.tk",
    is_forwarded   = True,
    message_id_hash= hashlib.sha256(b"<msgid>").hexdigest(),
)
```

---

### 3.4 Predictions

#### `log_prediction(email_event_id, model_version, phishing_prob, predicted_label, risk_level)`

Writes the ML result for an email event. One `Prediction` per `EmailEvent` — calling twice raises an error.

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `email_event_id` | `int` | ✅ | FK → `EmailEvent.id` |
| `model_version` | `str` | ✅ | Stem of the model `.joblib` filename, e.g. `"phishing_model_b"` |
| `phishing_prob` | `float` | ✅ | Always the **phishing** probability (`0.0` = safe, `1.0` = confirmed phishing). For trusted-domain bypasses this is `0.0`. |
| `predicted_label` | `str` | ✅ | `"phishing"` or `"legitimate"` |
| `risk_level` | `str` | ✅ | `"HIGH"`, `"MEDIUM"`, or `"LOW"` |

**Returns:** `Prediction` ORM object  
**Raises:**
- `ValueError("EmailEvent does not exist")` — bad `email_event_id`
- `ValueError("Prediction already exists for this EmailEvent")` — duplicate

```python
pred = db.log_prediction(
    email_event_id = event.id,
    model_version  = "phishing_model_b",
    phishing_prob  = 0.9987,
    predicted_label= "phishing",
    risk_level     = "HIGH",
)
```

---

### 3.5 Trusted Domains

#### `is_trusted_domain(user_id, domain)`

Returns `True` if `domain` is in the user's per-user trusted list.

```python
if db.is_trusted_domain(user.id, "internal.acme.com"):
    # skip model
```

---

#### `add_trusted_domain(user_id, domain, reason="")`

Adds a domain to the user's trust list. Idempotent — returns the existing record if already present.

| Parameter | Type | Notes |
|-----------|------|-------|
| `user_id` | `int` | FK → `User.id` |
| `domain` | `str` | Lowercase domain string, e.g. `"internal.acme.com"` |
| `reason` | `str` | Human-readable note, stored for auditing |

**Returns:** `TrustedDomain` ORM object

```python
db.add_trusted_domain(user.id, "internal.acme.com", reason="Company mail server")
```

---

### 3.6 Query Methods

#### `get_user_predictions(user_id, limit=100)`

Returns a joined list of email events and their predictions for a user, ordered newest-first.

**Returns:** `list[dict]`

Each dict:

```python
{
    "email_event_id": int,
    "user_id":        int,
    "sender_domain":  str,
    "is_forwarded":   bool,
    "received_at":    datetime,
    "message_id_hash":str | None,
    "prediction": None | {
        "prediction_id":       int,
        "model_version":       str,
        "phishing_probability":float,   # 0.0–1.0, always phishing likelihood
        "predicted_label":     str,     # "phishing" or "legitimate"
        "risk_level":          str,     # "HIGH" | "MEDIUM" | "LOW"
        "created_at":          datetime,
    }
}
```

`prediction` is `None` for events that were logged but never classified (should not occur in normal operation).

```python
history = db.get_user_predictions(user.id, limit=20)
for record in history:
    p = record["prediction"]
    print(record["sender_domain"], p["predicted_label"], p["phishing_probability"])
```

---

## 4. Database Schema

```
┌──────────────────────────────────────────────────┐
│  User                                            │
│  id            INTEGER  PK                       │
│  emailHash     TEXT     UNIQUE  NOT NULL         │ ← SHA-256(email)
│  passwordHash  TEXT     NOT NULL                 │
│  role          TEXT     DEFAULT 'normal'         │
│  firstName     TEXT                              │
│  lastName      TEXT                              │
│  mobileNumber  TEXT     UNIQUE                   │
│  address       TEXT                              │
│  createdAt     DATETIME DEFAULT now()            │
│  updatedAt     DATETIME DEFAULT now()            │
└──────────────────────────┬───────────────────────┘
                           │ 1:N
          ┌────────────────┴──────────────────────┐
          │                                       │
┌─────────▼───────────────────────┐   ┌──────────▼──────────────────────┐
│  EmailEvent                     │   │  TrustedDomain                  │
│  id             INTEGER  PK     │   │  id        INTEGER  PK          │
│  userId         INTEGER  FK     │   │  userId    INTEGER  FK          │
│  senderDomain   TEXT            │   │  domain    TEXT                 │
│  isForwarded    BOOLEAN         │   │  reason    TEXT                 │
│  receivedAt     DATETIME        │   │  createdAt DATETIME             │
│  messageIdHash  TEXT    UNIQUE  │   │  UNIQUE(userId, domain)         │
└─────────┬───────────────────────┘   └─────────────────────────────────┘
          │ 1:1
┌─────────▼───────────────────────┐
│  Prediction                     │
│  id                  INTEGER PK │
│  emailEventId        INTEGER FK │ UNIQUE
│  modelVersion        TEXT       │
│  phishingProbability FLOAT      │ ← always represents phishing likelihood
│  predictedLabel      TEXT       │ ← "phishing" | "legitimate"
│  riskLevel           TEXT       │ ← "HIGH" | "MEDIUM" | "LOW"
│  createdAt           DATETIME   │
└─────────────────────────────────┘
```

**Important:** `phishingProbability` is always normalised to represent the probability that the email **is phishing**:
- Model predicted `"phishing"` at 0.92 → stored as `0.92`
- Model predicted `"legitimate"` at 0.93 → stored as `1 − 0.93 = 0.07`
- Trusted-domain bypass → stored as `0.0`

---

## 5. ML Detector — `PhishingDetector`

**File:** `src/phishing_detector.py`

### 5.1 Initialisation

```python
from phishing_detector import PhishingDetector

detector = PhishingDetector(
    host             = "localhost",          # SMTP bind host (only used in standalone mode)
    port             = 1025,                 # SMTP bind port (only used in standalone mode)
    model_dir        = "models/model b/trainning2",  # None = auto-detect
    whitelist_domains= None,                 # None = use built-in defaults; set() = empty
)
```

On construction:
- Loads `phishing_model_b.joblib` (CalibratedClassifierCV wrapping LinearSVC)
- Loads `tfidf_vectorizer_b.joblib` (TfidfVectorizer, ngram_range=(1,3))

---

### 5.2 `classify_email(subject, body)`

Runs the ML model. Both arguments must already be **cleaned text** (run through `_clean_text()` first).

```python
result = detector.classify_email(subject, body)
```

**Returns:**

```python
{
    "label":       "phishing" | "legitimate",
    "probability": float   # probability of the WINNING class (not always phishing!)
}
```

> ⚠ **Normalisation required.** `probability` is the model's confidence in whichever label won. To get a consistent phishing likelihood for storage:
> ```python
> phishing_prob = result["probability"]
> if result["label"] == "legitimate":
>     phishing_prob = 1.0 - phishing_prob
> ```

---

### 5.3 `preprocess_email(raw_email)`

Full preprocessing pipeline: parse RFC-2822 bytes → extract subject + body → remove HTML/CSS/invisible characters → detect forwarded original sender.

```python
extracted = detector.preprocess_email(raw_bytes)
```

**Returns:** `dict` or `None` (on parse failure)

```python
{
    "subject":          str,   # cleaned subject text (for model input)
    "body":             str,   # cleaned body text (for model input)
    "original_subject": str,   # raw subject before cleaning (for auto-reply)
    "original_body":    str,   # raw body before cleaning
    "original_sender":  str | None  # email address extracted from forward headers
}
```

`original_sender` is extracted by `get_original_sender()` which looks for patterns like:
- `Forwarded message from: addr@domain.com`
- `From: addr@domain.com` in quoted text
- `X-Original-From` header

---

### 5.4 `is_whitelisted(email_address)`

Checks the global in-memory whitelist. Handles subdomains — e.g. `no-reply@accounts.google.com` matches `google.com` in the whitelist.

```python
detector.is_whitelisted("no-reply@accounts.google.com")  # True
detector.is_whitelisted("attacker@evil.tk")               # False
```

**Returns:** `bool`

---

## 6. Internal Helper Functions

These live in `smtp_server.py` and are not part of the public interface, but are useful to understand when extending the server.

| Function | Signature | Purpose |
|----------|-----------|---------|
| `hash_email` | `(email) → str` | `SHA-256(email.strip().lower())` — used for all user lookups |
| `get_sender_domain` | `(email) → str` | Extracts domain from email address |
| `_phishing_risk_level` | `(prob: float) → str` | Converts `phishing_probability` to `"HIGH"/"MEDIUM"/"LOW"` |
| `_message_id_hash` | `(raw_bytes) → str\|None` | `SHA-256(Message-Id header)` for deduplication |

---

## 7. Integration Guide

### 7.1 Registering a User

Before any email from a user's address will be processed, you must insert a `User` row. This is the onboarding step your registration endpoint / admin tool must call.

```python
import hashlib
from database import DatabaseManager

db   = DatabaseManager()

def h(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode()).hexdigest()

user = db.create_user(
    email_hash    = h("alice@gmail.com"),   # forwarding address they'll use
    password_hash = h("their_password"),
    first_name    = "Alice",
    last_name     = "Smith",
)
```

The user then sets up Gmail/Outlook auto-forwarding to point at `your-server:1025`. Every email they forward will be validated against this record.

---

### 7.2 Per-User Trusted Domains

Users can nominate domains they trust (e.g. their employer's mail server). Emails originating from these domains bypass the ML model and are always classified as `legitimate`.

```python
db.add_trusted_domain(user.id, "internal.acme.com", reason="Company mail server")
db.add_trusted_domain(user.id, "acme.com",          reason="Company domain")
```

To remove a trusted domain, use a direct SQLAlchemy delete — `DatabaseManager` does not expose a `remove_trusted_domain()` method (add one in `database.py` if needed).

**Priority order for trust checks (evaluated in this order, first match wins):**
1. Global in-memory whitelist (`DETECTOR.is_whitelisted(check_address)`)
2. Per-user DB trusted domain (`DB_MANAGER.is_trusted_domain(user.id, check_domain)`)
3. ML model (if neither of the above matched)

---

### 7.3 Reading Scan History

```python
records = db.get_user_predictions(user_id=42, limit=50)

for r in records:
    p = r["prediction"]
    if p and p["risk_level"] == "HIGH":
        print(f"HIGH-RISK email from {r['sender_domain']} at {r['received_at']}")
        print(f"  → {p['phishing_probability']:.0%} phishing confidence")
```

---

### 7.4 Programmatic Embedding

To embed the server inside another Python process (instead of running `smtp_server.py` as a standalone script):

```python
import smtp_server as srv
from database import DatabaseManager
from phishing_detector import PhishingDetector
from pathlib import Path

srv.DB_MANAGER    = DatabaseManager()
srv.DETECTOR      = PhishingDetector()
srv.MODEL_VERSION = Path(srv.DETECTOR.model_path).stem
srv.REPLY_CFG     = {
    "enabled":   True,
    "host":      "smtp.yourrelay.com",
    "port":      587,
    "from_addr": "scanner@yourdomain.com",
}

handler    = srv.RegisteredUserSMTPHandler()
controller = srv.start_controller(handler, host="0.0.0.0", port=1025)

# controller.stop() to shut down
```

---

## 8. Error Reference

| Exception | Raised by | Meaning |
|-----------|-----------|---------|
| `ValueError("User with this email hash already exists")` | `create_user()` | Duplicate registration attempt |
| `ValueError("EmailEvent does not exist")` | `log_prediction()` | Bad `email_event_id` passed |
| `ValueError("Prediction already exists for this EmailEvent")` | `log_prediction()` | Called twice for the same event |
| `RuntimeError("SMTP server not initialized")` | `handle_smtp_email()` | Called before setting `DB_MANAGER` / `DETECTOR` globals |
| `InconsistentVersionWarning` (sklearn) | model load | Model was saved with a different sklearn version. Pin `scikit-learn~=1.6.1` in your environment. |

---

## 9. End-to-End Test

A full integration test with no mocks is included at `tools/test_e2e.py`. It starts two real SMTP servers (main + reply capture), sends 6 emails via `smtplib`, reads back the DB, and prints decoded reply subjects.

```bash
cd path/to/phishing-project
python -W ignore tools/test_e2e.py
```

Expected output summary:
```
SMTP responses : 6 PASS  /  0 FAIL
DB records     : 5
Replies sent   : 5
```

(The unregistered-sender case produces a `550` and no DB record — hence 6 emails sent but only 5 DB records.)
