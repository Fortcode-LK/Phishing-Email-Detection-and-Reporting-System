"""One-time initialization and demonstration script for the phishing detector DB."""
from __future__ import annotations

import hashlib
import secrets
from pprint import pprint

from database import DatabaseManager


def generate_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def main() -> None:
    manager = DatabaseManager()

    unique_suffix = secrets.token_hex(4)
    plain_email = f"demo+{unique_suffix}@example.com"
    email_hash = generate_hash(plain_email)
    password_hash = generate_hash(secrets.token_hex(16))

    print("Creating demo user …")
    user = manager.create_user(
        email_hash=email_hash,
        password_hash=password_hash,
        first_name="Demo",
        last_name="User",
        mobile_number=f"+1555{secrets.randbelow(10_000):04d}",
        address="123 Example Street",
    )
    print(f"  → User ID: {user.id}")

    print("Fetching user by email hash …")
    fetched_user = manager.get_user_by_email_hash(email_hash)
    print(f"  → Retrieved: {fetched_user.firstName} {fetched_user.lastName}")

    print("Adding a trusted domain …")
    trusted_domain = manager.add_trusted_domain(user.id, "example.com", reason="Corporate domain")
    print(f"  → Trusted domain ID: {trusted_domain.id}")

    print("Checking trusted domain status …")
    is_trusted = manager.is_trusted_domain(user.id, "example.com")
    print(f"  → is_trusted? {is_trusted}")

    print("Logging an email event …")
    email_event = manager.log_email_event(
        user_id=user.id,
        sender_domain="alerts.bad-domain.test",
        is_forwarded=True,
        message_id_hash=secrets.token_hex(12),
    )
    print(f"  → EmailEvent ID: {email_event.id}")

    print("Logging a prediction …")
    prediction = manager.log_prediction(
        email_event_id=email_event.id,
        model_version="model-a-1.0",
        phishing_prob=0.92,
        predicted_label="phishing",
        risk_level="HIGH",
    )
    print(f"  → Prediction ID: {prediction.id}")

    print("Retrieving recent predictions …")
    records = manager.get_user_predictions(user.id, limit=10)
    for idx, record in enumerate(records, start=1):
        print(f"--- Record #{idx} ---")
        pprint(record)

    print("Demo complete. SQLite file: phishing_detector.db")


if __name__ == "__main__":
    main()
