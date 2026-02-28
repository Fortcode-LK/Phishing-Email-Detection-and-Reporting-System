"""SMTP server that only processes emails from registered users."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import traceback
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Optional

from aiosmtpd.controller import Controller

from database import DatabaseManager
from phishing_detector import PhishingDetector

DB_MANAGER: Optional[DatabaseManager] = None
DETECTOR: Optional[PhishingDetector] = None
MODEL_VERSION: str = "unknown"


def hash_email(email: Optional[str]) -> str:
    if not email:
        return ""
    normalized = email.strip().lower()
    if not normalized:
        return ""
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_sender_domain(sender_email: Optional[str]) -> str:
    if not sender_email or "@" not in sender_email:
        return ""
    return sender_email.split("@")[-1].lower()


def _phishing_risk_level(probability: float) -> str:
    if probability >= 0.85:
        return "HIGH"
    if probability >= 0.55:
        return "MEDIUM"
    return "LOW"


def _message_id_hash(raw_message: bytes) -> Optional[str]:
    try:
        parser = BytesParser(policy=policy.default)
        msg = parser.parsebytes(raw_message)
        message_id = msg.get("Message-Id")
        if message_id:
            return hashlib.sha256(message_id.encode("utf-8")).hexdigest()
    except Exception:
        pass
    return None


def handle_smtp_email(sender_email, recipients, raw_message):
    if DB_MANAGER is None or DETECTOR is None:
        raise RuntimeError("SMTP server not initialized")

    user = DB_MANAGER.get_user_by_email_hash(hash_email(sender_email))
    if not user:
        print(f"DISCARDED: Unregistered sender {sender_email}")
        return "250 OK"

    extracted = DETECTOR.preprocess_email(raw_message)
    if not extracted:
        print(f"DISCARDED: Failed preprocessing for user_id={user.id}")
        return "550 Unable to process message"

    sender_domain = get_sender_domain(sender_email)
    message_id_hash = _message_id_hash(raw_message)

    email_event = DB_MANAGER.log_email_event(
        user_id=user.id,
        sender_domain=sender_domain,
        is_forwarded=bool(extracted.get("original_sender")),
        message_id_hash=message_id_hash,
    )

    prediction = DETECTOR.classify_email(extracted["subject"], extracted["body"])
    phishing_probability = prediction["probability"]
    if prediction["label"] == "legitimate":
        phishing_probability = 1.0 - phishing_probability

    risk_level = _phishing_risk_level(phishing_probability)

    DB_MANAGER.log_prediction(
        email_event_id=email_event.id,
        model_version=MODEL_VERSION,
        phishing_prob=phishing_probability,
        predicted_label=prediction["label"],
        risk_level=risk_level,
    )

    print(
        f"PROCESSED for user_id={user.id}: "
        f"{prediction['label'].upper()} {phishing_probability:.2%}"
    )

    return "250 Message accepted for delivery"


class RegisteredUserSMTPHandler:
    async def handle_DATA(self, server, session, envelope):
        try:
            return handle_smtp_email(
                sender_email=envelope.mail_from,
                recipients=envelope.rcpt_tos,
                raw_message=envelope.content,
            )
        except Exception as exc:
            print(f"ERROR: Handler failure {exc}")
            traceback.print_exc()
            return "451 Temporary server error"


def _resolve_whitelist(args) -> Optional[set[str]]:
    if args.no_whitelist:
        return set()
    if not args.whitelist:
        return None
    defaults = {
        "google.com",
        "gmail.com",
        "redditmail.com",
        "reddit.com",
        "github.com",
        "microsoft.com",
        "amazon.com",
        "paypal.com",
        "apple.com",
        "linkedin.com",
        "twitter.com",
        "facebook.com",
        "instagram.com",
    }
    defaults.update({domain.lower() for domain in args.whitelist})
    return defaults


def start_controller(handler, host: str, port: int) -> Controller:
    controller = Controller(handler, hostname=host, port=port)
    controller.start()
    print(f"SMTP router listening on {host}:{port}")
    print("Waiting for emails... (Ctrl+C to quit)")
    return controller


def main() -> None:
    parser = argparse.ArgumentParser(description="SMTP router for phishing detector")
    parser.add_argument("--host", default="localhost", help="SMTP bind host")
    parser.add_argument("--port", type=int, default=1025, help="SMTP bind port")
    parser.add_argument("--model-dir", default=None, help="Path to model directory")
    parser.add_argument(
        "--whitelist",
        nargs="*",
        help="Additional domains to whitelist for the detector",
    )
    parser.add_argument(
        "--no-whitelist",
        action="store_true",
        help="Disable builtin whitelisting",
    )

    args = parser.parse_args()

    whitelist = _resolve_whitelist(args)

    global DB_MANAGER, DETECTOR, MODEL_VERSION
    DB_MANAGER = DatabaseManager()
    DETECTOR = PhishingDetector(
        host=args.host,
        port=args.port,
        model_dir=args.model_dir,
        whitelist_domains=whitelist,
    )
    MODEL_VERSION = Path(DETECTOR.model_path).stem

    handler = RegisteredUserSMTPHandler()
    controller = start_controller(handler, args.host, args.port)

    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("\nShutting down SMTP router...")
    finally:
        controller.stop()
        print("SMTP router stopped")


if __name__ == "__main__":
    main()
