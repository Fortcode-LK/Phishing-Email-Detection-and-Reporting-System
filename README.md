# Phishing Email Detection System

3-step phishing detection system using SMTP server, email preprocessing, and machine learning classification.

## Features

- **SMTP Server**: Receives emails on localhost (configurable port)
- **Email Preprocessing**: Aggressive text cleaning, HTML/Unicode removal, forwarded email extraction
- **ML Classification**: TF-IDF vectorization + pre-trained model
- **Domain Whitelisting**: Auto-classify trusted senders (Google, Reddit, GitHub, etc.)
- **Real-time Processing**: Classify emails as they arrive

## Quick Start

See [QUICKSTART.md](QUICKSTART.md) for installation and usage.

## Project Structure

```
phishing-project/
├── src/
│   └── phishing_detector.py    # Core detection system
├── tools/
│   └── gmail_forwarder.py       # Testing utility for Gmail
├── models/
│   └── model b/trainning2/      # Pre-trained ML models
├── requirements.txt             # Python dependencies
└── docs/                        # Documentation
```

## Documentation

- [QUICKSTART.md](QUICKSTART.md) - Installation and basic usage
- [USAGE.md](USAGE.md) - Detailed usage and configuration
- [GMAIL_TESTING.md](GMAIL_TESTING.md) - Testing with real Gmail emails

## Requirements

- Python 3.8+
- aiosmtpd
- scikit-learn
- beautifulsoup4
- joblib

## License

See repository license.
