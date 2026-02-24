# Phishing Detection System - Quick Start

## What This Does

A complete 3-step phishing email detection system:
1. **SMTP Server** - Receives emails via SMTP on localhost:1025
2. **Smart Preprocessing** - Extracts original content from forwarded emails
3. **ML Classification** - Detects phishing using trained scikit-learn model

## Installation

```bash
cd phishing-project
pip install -r requirements.txt
```

## Usage

### Option 1: Run Demo (No SMTP Server)

Test the classifier directly with sample emails:

```bash
cd src
python demo.py
```

This will:
- Load the trained model
- Classify 5 test emails (phishing and legitimate)
- Show extraction from forwarded emails
- Display accuracy metrics

### Option 2: Run Full SMTP Server

**Terminal 1 - Start the detector:**
```bash
cd src
python phishing_detector.py
```

**Terminal 2 - Send test emails:**
```bash
cd src
python test_email_sender.py
```

You'll see real-time classification results in Terminal 1.

### Option 3: Forward Real Emails

1. Start the detector: `python phishing_detector.py`
2. Forward emails to localhost:1025 using any SMTP client

Example with Python:
```python
import smtplib
from email.mime.text import MIMEText

msg = MIMEText("Suspicious email content here")
msg['Subject'] = 'Fwd: Urgent - Verify Your Account'
msg['From'] = 'you@example.com'

with smtplib.SMTP('localhost', 1025) as server:
    server.send_message(msg)
```

## Files Created

```
phishing-project/
├── src/
│   ├── phishing_detector.py     # Main 3-step detector
│   ├── test_email_sender.py     # Send test emails
│   └── demo.py                  # Standalone demo
├── requirements.txt             # Python dependencies
└── USAGE.md                     # Detailed documentation
```

## Expected Output Example

```
SMTP Server started on localhost:1025
Waiting for emails...

============================================================
Received email from: test.user@example.com
============================================================

Extracted Subject: urgent: your account has been suspended
Extracted Body: your paypal account has been suspended...

============================================================
CLASSIFICATION RESULT:
  Sender: test.user@example.com
  Label: PHISHING
  Probability: 94.23%
============================================================
```

## Key Features

✓ **Handles Forwarded Emails** - Automatically extracts original content  
✓ **Clean Text Processing** - Removes signatures, headers, HTML tags  
✓ **High Accuracy** - Uses trained TF-IDF + classification model  
✓ **Easy Testing** - Included test email sender  
✓ **No External Services** - Runs completely offline on localhost  

## Next Steps

1. Run the demo: `python src/demo.py`
2. Try the full server: `python src/phishing_detector.py`
3. Send test emails: `python src/test_email_sender.py`
4. Read detailed docs: See `USAGE.md`

## Troubleshooting

**"Port 1025 already in use"**
```bash
python phishing_detector.py --port 2525
python test_email_sender.py --port 2525
```

**"Model files not found"**
- Ensure you have the trained models in: `models/model b/trainning2/`
- Files needed: `phishing_model_b.joblib` and `tfidf_vectorizer_b.joblib`

**"aiosmtpd not installed"**
```bash
pip install -r requirements.txt
```
