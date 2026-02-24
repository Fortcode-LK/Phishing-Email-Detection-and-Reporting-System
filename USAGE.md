# Phishing Detection System - Usage Guide

## Overview

This system implements a 3-step phishing detection pipeline:
1. **SMTP Server** - Receives emails on localhost:1025
2. **Email Preprocessing** - Extracts and cleans content from forwarded emails
3. **ML Classification** - Uses trained model to detect phishing

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the System

### Start the Phishing Detector Server

```bash
cd src
python phishing_detector.py
```

**Options:**
- `--host` - SMTP server host (default: localhost)
- `--port` - SMTP server port (default: 1025)
- `--model-dir` - Custom model directory path

**Example:**
```bash
python phishing_detector.py --host localhost --port 1025
```

### Send Test Emails

In a separate terminal:

```bash
cd src
python test_email_sender.py
```

**Send specific email types:**
```bash
# Send only phishing email
python test_email_sender.py --type phishing

# Send only legitimate email
python test_email_sender.py --type legitimate

# Send forwarded phishing email
python test_email_sender.py --type forwarded

# Send all test emails (default)
python test_email_sender.py --type all
```

## How It Works

### STEP 1: Receive Email via SMTP
- SMTP server listens on localhost:1025
- Accepts incoming email connections
- Extracts sender and raw message content

### STEP 2: Preprocess Email
- Parses email headers and body
- Detects forwarded emails (Fwd: prefix)
- Extracts original content from forwarding markers:
  - "---------- Forwarded message ---------"
  - "Forwarded by Gmail"
  - "Begin forwarded message:"
- Removes signatures and footers
- Cleans text (lowercase, normalize whitespace)

### STEP 3: Model Classification
- Loads pre-trained model from `models/model b/trainning2/`
- Combines subject + body as input
- Transforms text using TF-IDF vectorizer
- Returns classification:
  - **Label**: 'phishing' or 'legitimate'
  - **Probability**: confidence score (0-1)

## Example Output

```
SMTP Server started on localhost:1025
Waiting for emails... (Press Ctrl+C to stop)

============================================================
Received email from: test.user@example.com
Recipients: ['phishing-detector@localhost']
============================================================

Extracted Subject: urgent: your account has been suspended
Extracted Body: your paypal account has been temporarily suspended...

============================================================
CLASSIFICATION RESULT:
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
- `models/model b/trainning2/phishing_model_b.joblib`
- `models/model b/trainning2/tfidf_vectorizer_b.joblib`

These must exist for the system to work.

## Troubleshooting

**Port already in use:**
```bash
python phishing_detector.py --port 1026
```

**Model not found:**
- Verify files exist in `models/model b/trainning2/`
- Or specify custom path: `--model-dir /path/to/models`

**Cannot send test emails:**
- Ensure detector server is running first
- Check firewall settings for localhost connections

## Security Notes

- This server is for **LOCAL TESTING ONLY**
- Do not expose to external networks
- Runs on localhost by default for security
- No authentication implemented (testing purposes)
