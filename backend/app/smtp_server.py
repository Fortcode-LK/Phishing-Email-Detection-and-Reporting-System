"""SMTP server that only processes emails from registered users."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import smtplib
import traceback
from email import policy
from email.mime.text import MIMEText
from email.parser import BytesParser
from email.utils import formatdate
from pathlib import Path
from typing import Optional

from aiosmtpd.controller import Controller

from database import DatabaseManager
from phishing_detector import PhishingDetector

DB_MANAGER: Optional[DatabaseManager] = None
DETECTOR: Optional[PhishingDetector] = None
MODEL_VERSION: str = "unknown"

REPLY_CFG: dict = {
    "enabled": False,
    "host": "localhost",
    "port": 25,
    "from_addr": "phishing-scanner@localhost",
}


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


def send_scan_reply(
    to_addr: str,
    original_subject: str,
    predicted_label: str,
    phishing_probability: float,
    risk_level: str,
    reason: str,
) -> None:
    """Send a scan-result email back to the user's forwarding address.

    Uses smtplib (stdlib) so no extra dependencies are needed.
    Failures are logged but never propagate — the reply is best-effort.
    """
    if not REPLY_CFG.get("enabled"):
        return

    pct = phishing_probability * 100
    if predicted_label == "phishing":
        verdict_line = f"⚠  PHISHING detected  ({pct:.0f}% confidence)"
        action_line  = "We recommend you DO NOT click any links or open attachments."
    else:
        verdict_line = f"✔  Safe  ({100 - pct:.0f}% confidence)"
        action_line  = "No threats were detected in this email."

    scanned_subject = original_subject.strip() if original_subject else "(no subject)"

    body = (
        f"Phishing Scan Result\n"
        f"{'=' * 40}\n"
        f"Scanned email : {scanned_subject}\n"
        f"Verdict       : {verdict_line}\n"
        f"Risk level    : {risk_level}\n"
        f"Checked via   : {reason}\n"
        f"{'=' * 40}\n"
        f"{action_line}\n\n"
        f"-- Phishing Detection System"
    )

    msg = MIMEText(body, "plain", "utf-8")
    msg["From"]    = REPLY_CFG["from_addr"]
    msg["To"]      = to_addr
    msg["Date"]    = formatdate(localtime=True)
    msg["Subject"] = f"[Phishing Scan] {'⚠ PHISHING' if predicted_label == 'phishing' else '✔ Safe'} – {scanned_subject}"

    try:
        with smtplib.SMTP(REPLY_CFG["host"], REPLY_CFG["port"], timeout=10) as relay:
            relay.sendmail(REPLY_CFG["from_addr"], [to_addr], msg.as_bytes())
        print(f"REPLY     sent to {to_addr}")
    except Exception as exc:
        print(f"REPLY     FAILED to {to_addr}: {exc}")


def handle_smtp_email(sender_email, recipients, raw_message):
    if DB_MANAGER is None or DETECTOR is None:
        raise RuntimeError("SMTP server not initialized")

    user = DB_MANAGER.get_user_by_email_hash(hash_email(sender_email))
    if not user:
        print(f"DISCARDED: Unregistered sender {sender_email}")
        return "550 Rejected - sender not registered"

    extracted = DETECTOR.preprocess_email(raw_message)
    if not extracted:
        print(f"DISCARDED: Failed preprocessing for user_id={user.id}")
        return "550 Rejected - message could not be parsed"

    original_sender = extracted.get("original_sender")
    original_domain = get_sender_domain(original_sender) if original_sender else None

    check_address = original_sender if original_sender else sender_email
    check_domain  = original_domain if original_domain else get_sender_domain(sender_email)

    message_id_hash = _message_id_hash(raw_message)

    email_event = DB_MANAGER.log_email_event(
        user_id=user.id,
        sender_domain=check_domain,
        is_forwarded=bool(original_sender),
        message_id_hash=message_id_hash,
    )

    trusted_address: Optional[str] = None
    if DETECTOR.is_whitelisted(check_address):
        trusted_address = check_address
    elif DB_MANAGER.is_trusted_domain(user.id, check_domain):
        trusted_address = check_address

    if trusted_address:
        predicted_label = "legitimate"
        phishing_probability = 0.0
        risk_level = "LOW"
        reason = "trusted_domain"
        print(
            f"TRUSTED  user_id={user.id} | {trusted_address} → skipping model"
        )
    else:
        prediction = DETECTOR.classify_email(extracted["subject"], extracted["body"])
        predicted_label = prediction["label"]
        phishing_probability = prediction["probability"]
        if predicted_label == "legitimate":
            phishing_probability = 1.0 - phishing_probability
        risk_level = _phishing_risk_level(phishing_probability)
        reason = "model_prediction"

    DB_MANAGER.log_prediction(
        email_event_id=email_event.id,
        model_version=MODEL_VERSION,
        phishing_prob=phishing_probability,
        predicted_label=predicted_label,
        risk_level=risk_level,
    )

    print(
        f"PROCESSED user_id={user.id} | {predicted_label.upper()} "
        f"{phishing_probability:.2%} [{risk_level}] via {reason}"
    )

    send_scan_reply(
        to_addr=sender_email,
        original_subject=extracted.get("original_subject", ""),
        predicted_label=predicted_label,
        phishing_probability=phishing_probability,
        risk_level=risk_level,
        reason=reason,
    )

    return "250 OK - processed successfully"


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
            return "421 Temp fail - try again later"


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
    parser.add_argument(
        "--reply",
        action="store_true",
        help="Enable auto-reply: send scan result back to the forwarding user",
    )
    parser.add_argument(
        "--reply-host",
        default="localhost",
        help="Outbound SMTP relay host for sending replies (default: localhost)",
    )
    parser.add_argument(
        "--reply-port",
        type=int,
        default=25,
        help="Outbound SMTP relay port (default: 25)",
    )
    parser.add_argument(
        "--reply-from",
        default="phishing-scanner@localhost",
        help="From address used in scan-result reply emails",
    )

    args = parser.parse_args()

    whitelist = _resolve_whitelist(args)

    global DB_MANAGER, DETECTOR, MODEL_VERSION, REPLY_CFG
    REPLY_CFG["enabled"]   = args.reply
    REPLY_CFG["host"]      = args.reply_host
    REPLY_CFG["port"]      = args.reply_port
    REPLY_CFG["from_addr"] = args.reply_from
    if args.reply:
        print(
            f"Auto-reply  ENABLED → relay {args.reply_host}:{args.reply_port} "
            f"from <{args.reply_from}>"
        )
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
