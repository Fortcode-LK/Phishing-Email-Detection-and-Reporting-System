# Testing with Real Gmail Emails

## Quick Setup (3 Steps)

### Step 1: Start the Phishing Detector

In **Terminal 1**:
```powershell
cd C:\Users\jkiri\Downloads\phishing-project\phishing-project\src
python phishing_detector.py
```

Keep this terminal open - it will show classification results.

### Step 2: Get Gmail App Password

1. Go to https://myaccount.google.com/apppasswords
2. Sign in to your Gmail account
3. Click "Create" and name it (e.g., "Phishing Detector")
4. Copy the 16-character password (you'll need this in Step 3)

**Note:** If you don't see App Passwords:
- Enable 2-Step Verification first in your Google Account
- Then App Passwords will appear in Security settings

### Step 3: Forward Gmail Emails

In **Terminal 2**:
```powershell
cd C:\Users\jkiri\Downloads\phishing-project\phishing-project\tools
python gmail_forwarder.py
```

Follow the prompts:
- Choose option `1` (Fetch from Gmail via IMAP)
- Enter your Gmail address
- Paste the App Password from Step 2
- Choose search criteria (or press Enter for "ALL")

## Usage Methods

### Method 1: Automatic IMAP Fetch (Recommended)

```powershell
# Change to tools directory
cd tools

# Interactive mode
python gmail_forwarder.py

# Command line mode - fetch latest 5 emails
python gmail_forwarder.py --gmail your.email@gmail.com --fetch

# Fetch only unread emails
python gmail_forwarder.py --gmail your.email@gmail.com --fetch --search UNSEEN

# Fetch emails with "urgent" in subject
python gmail_forwarder.py --gmail your.email@gmail.com --fetch --search 'SUBJECT "urgent"'

# Fetch more emails
python gmail_forwarder.py --gmail your.email@gmail.com --fetch --limit 10
```

### Method 2: Manual Copy/Paste

1. Run: `python tools/gmail_forwarder.py`
2. Choose option `2`
3. In Gmail:
   - Open any email
   - Click three dots (⋮) → **Show original**
   - Click **Copy to clipboard**
4. Paste into the terminal
5. Press **Ctrl+Z** then **Enter** (Windows) to finish

### Method 3: Forward Specific Email

Save email to file first:

**In Gmail:**
- Open email → Show original → Download original
- Save as `email.eml`

**In Terminal:**
```powershell
python -c "import smtplib; from email import message_from_file, policy; msg = message_from_file(open('email.eml', 'rb'), policy=policy.default); smtplib.SMTP('localhost', 1025).send_message(msg)"
```

## Expected Output

**Terminal 1 (Phishing Detector):**
```
============================================================
Received email from: sender@example.com
Recipients: ['your.email@gmail.com']
============================================================

Extracted Subject: urgent: verify your account now
Extracted Body: dear customer, your account has been...

============================================================
CLASSIFICATION RESULT:
  Sender: sender@example.com
  Label: PHISHING
  Probability: 87.45%
============================================================
```

**Terminal 2 (Gmail Forwarder):**
```
Found 3 email(s) to process

----------------------------------------------------------------------
Processing email 1/3...
----------------------------------------------------------------------
From: suspicious@sender.com
Subject: Urgent: Account Verification Required
Date: Mon, 24 Feb 2026 10:30:00 +0000
✓ Forwarded to localhost:1025
```

## Troubleshooting

### "Authentication failed"
- Make sure you're using an **App Password**, not your regular Gmail password
- Create one at: https://myaccount.google.com/apppasswords
- Enable 2-Step Verification if needed

### "Connection refused to localhost:1025"
- Make sure the phishing detector is running first
- Check that nothing else is using port 1025
- Try a different port: `python phishing_detector.py --port 2525`

### "IMAP not enabled"
- Go to Gmail Settings → Forwarding and POP/IMAP
- Enable IMAP access
- Save changes and try again

### Firewall blocking localhost
- Windows Firewall should allow localhost connections by default
- If blocked, allow Python through Windows Firewall

## Testing Flow

1. **Start detector** (Terminal 1):
   ```powershell
   python phishing_detector.py
   ```

2. **Forward Gmail emails** (Terminal 2):
   ```powershell
   cd tools
   python gmail_forwarder.py
   ```

3. **View results** in Terminal 1 in real-time

4. **Test different emails:**
   - Forwarded emails (should extract original content)
   - Spam emails (should detect phishing)
   - Regular emails (should classify as legitimate)

## Security Notes

⚠️ **Important:**
- App Passwords are specific to your device - don't share them
- The detector runs on localhost only (not accessible from internet)
- Emails are processed in memory and not stored
- Revoke App Password when done testing

## Advanced: Fetch Specific Gmail Labels

```powershell
# Change to tools directory first
cd tools

# Fetch from a specific folder
python gmail_forwarder.py --gmail you@gmail.com --fetch --search 'X-GM-LABELS "Spam"'

# Fetch emails from last 7 days
python gmail_forwarder.py --gmail you@gmail.com --fetch --search 'SINCE 17-Feb-2026'

# Fetch from specific sender
python gmail_forwarder.py --gmail you@gmail.com --fetch --search 'FROM "suspicious@sender.com"'
```

## Next Steps

After testing with real emails:
1. Review classification accuracy in the detector output
2. Try forwarding both legitimate and suspicious emails
3. Test forwarded email extraction with "Fwd:" subjects
4. Check if preprocessing correctly handles HTML emails
