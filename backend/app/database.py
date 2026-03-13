"""SQLite-backed database utilities for the phishing detector."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List

from sqlalchemy import create_engine, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from models import Base, EmailEvent, Prediction, TrustedDomain, User

_DB_PATH = Path(__file__).resolve().parents[2] / "phishing_detector.db"
DATABASE_URL = f"sqlite:///{_DB_PATH}"


class DatabaseManager:
    """High-level database helper that wraps SQLAlchemy sessions."""

    def __init__(self):
        self.engine = create_engine(
            DATABASE_URL,
            echo=False,
            future=True,
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(self.engine)
        self._migrate_remove_mobile_unique()
        self._migrate_add_email_alerts()
        self._Session = sessionmaker(
            bind=self.engine,
            future=True,
            expire_on_commit=False,
        )

    def _migrate_remove_mobile_unique(self) -> None:
        with self.engine.connect() as conn:
            schema = conn.execute(
                text("SELECT sql FROM sqlite_master WHERE type='table' AND name='User'")
            ).scalar() or ""
            if '"mobileNumber" VARCHAR UNIQUE' not in schema and "mobileNumber" not in schema.replace(" ", "").lower() or "unique" not in schema.lower():
                return
            lines = [l.strip() for l in schema.splitlines()]
            needs_migration = any(
                "mobilenumber" in l.lower() and "unique" in l.lower()
                for l in lines
            )
            if not needs_migration:
                return

            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS "User_migration_tmp" (
                    id INTEGER NOT NULL PRIMARY KEY,
                    "emailHash" VARCHAR NOT NULL UNIQUE,
                    "passwordHash" VARCHAR NOT NULL,
                    role VARCHAR,
                    "firstName" VARCHAR,
                    "lastName" VARCHAR,
                    "mobileNumber" VARCHAR,
                    address VARCHAR,
                    "createdAt" DATETIME,
                    "updatedAt" DATETIME
                )
            """))
            conn.execute(text("""
                INSERT INTO "User_migration_tmp"
                SELECT id, "emailHash", "passwordHash", role, "firstName",
                       "lastName", "mobileNumber", address, "createdAt", "updatedAt"
                FROM "User"
            """))
            conn.execute(text('DROP TABLE "User"'))
            conn.execute(text('ALTER TABLE "User_migration_tmp" RENAME TO "User"'))
            conn.commit()

    def _migrate_add_email_alerts(self) -> None:
        with self.engine.connect() as conn:
            schema = conn.execute(
                text("SELECT sql FROM sqlite_master WHERE type='table' AND name='User'")
            ).scalar() or ""
            if "emailAlertsEnabled" not in schema:
                conn.execute(text('ALTER TABLE "User" ADD COLUMN "emailAlertsEnabled" BOOLEAN NOT NULL DEFAULT 0'))
                conn.commit()

    @contextmanager
    def _session_scope(self) -> Session:
        session = self._Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_user(
        self,
        email_hash,
        password_hash,
        first_name=None,
        last_name=None,
        mobile_number=None,
        address=None,
    ):
        with self._session_scope() as session:
            if session.scalar(select(User).where(User.emailHash == email_hash)):
                raise ValueError("User with this email hash already exists")

            user = User(
                emailHash=email_hash,
                passwordHash=password_hash,
                firstName=first_name,
                lastName=last_name,
                mobileNumber=mobile_number,
                address=address,
            )
            session.add(user)
            try:
                session.flush()
            except IntegrityError as exc:
                session.rollback()
                raise ValueError(f"Database constraint violation: {exc.orig}") from exc
            return user

    def get_user_by_email_hash(self, email_hash):
        with self._session_scope() as session:
            return session.scalar(select(User).where(User.emailHash == email_hash))

    def ensure_admin_user(self, email_hash: str, password_hash: str) -> None:
        """Create the single admin account only if no admin user exists yet."""
        with self._session_scope() as session:
            existing = session.scalar(select(User).where(User.role == "admin"))
            if existing:
                return
            admin = User(
                emailHash=email_hash,
                passwordHash=password_hash,
                firstName="Admin",
                lastName="",
                role="admin",
            )
            session.add(admin)

    def get_email_alerts_enabled(self, user_id: int) -> bool:
        with self._session_scope() as session:
            user = session.get(User, user_id)
            if not user:
                return False
            return bool(user.emailAlertsEnabled)

    def set_email_alerts_enabled(self, user_id: int, enabled: bool) -> bool:
        with self._session_scope() as session:
            user = session.get(User, user_id)
            if not user:
                raise ValueError("User not found")
            user.emailAlertsEnabled = enabled
            return enabled

    def log_email_event(self, user_id, sender_domain, is_forwarded=False, message_id_hash=None):
        if message_id_hash:
            with self._session_scope() as session:
                existing = session.scalar(
                    select(EmailEvent).where(EmailEvent.messageIdHash == message_id_hash)
                )
                if existing:
                    return existing
        with self._session_scope() as session:
            event = EmailEvent(
                userId=user_id,
                senderDomain=sender_domain,
                isForwarded=is_forwarded,
                messageIdHash=message_id_hash,
            )
            session.add(event)
            return event

    def log_prediction(self, email_event_id, model_version, phishing_prob, predicted_label, risk_level):
        with self._session_scope() as session:
            if not session.get(EmailEvent, email_event_id):
                raise ValueError("EmailEvent does not exist")

            if session.scalar(select(Prediction).where(Prediction.emailEventId == email_event_id)):
                return None

            prediction = Prediction(
                emailEventId=email_event_id,
                modelVersion=model_version,
                phishingProbability=phishing_prob,
                predictedLabel=predicted_label,
                riskLevel=risk_level,
            )
            session.add(prediction)
            return prediction

    def is_trusted_domain(self, user_id, domain):
        with self._session_scope() as session:
            return (
                session.scalar(
                    select(TrustedDomain).where(
                        TrustedDomain.userId == user_id,
                        TrustedDomain.domain == domain,
                    )
                )
                is not None
            )

    def add_trusted_domain(self, user_id, domain, reason=""):
        with self._session_scope() as session:
            existing = session.scalar(
                select(TrustedDomain).where(
                    TrustedDomain.userId == user_id,
                    TrustedDomain.domain == domain,
                )
            )
            if existing:
                return existing

            trusted = TrustedDomain(
                userId=user_id,
                domain=domain,
                reason=reason,
            )
            session.add(trusted)
            return trusted

    def get_user_trusted_domains(self, user_id: int) -> list[dict]:
        """Return all trusted domains for a user."""
        with self._session_scope() as session:
            rows = session.execute(
                select(TrustedDomain)
                .where(TrustedDomain.userId == user_id)
                .order_by(TrustedDomain.createdAt.desc())
            ).scalars().all()
            return [
                {
                    "id": r.id,
                    "domain": r.domain,
                    "reason": r.reason or "",
                    "created_at": r.createdAt,
                }
                for r in rows
            ]

    def remove_trusted_domain(self, user_id: int, domain: str) -> bool:
        """Delete a trusted domain entry. Returns True if it existed."""
        with self._session_scope() as session:
            row = session.scalar(
                select(TrustedDomain).where(
                    TrustedDomain.userId == user_id,
                    TrustedDomain.domain == domain,
                )
            )
            if not row:
                return False
            session.delete(row)
            return True

    def get_user_summary(self, user_id: int, trend_days: int = 14) -> Dict[str, object]:
        """Return per-user aggregate stats + daily trend data.

        Used by GET /api/user/summary so the frontend never derives counts
        from a page-limited record set.
        """
        with self._session_scope() as session:
            total_scanned: int = session.scalar(
                select(func.count())
                .select_from(EmailEvent)
                .where(EmailEvent.userId == user_id)
            ) or 0

            total_phishing: int = session.scalar(
                select(func.count())
                .select_from(Prediction)
                .join(EmailEvent, EmailEvent.id == Prediction.emailEventId)
                .where(
                    EmailEvent.userId == user_id,
                    Prediction.predictedLabel == "phishing",
                )
            ) or 0

            total_legitimate: int = session.scalar(
                select(func.count())
                .select_from(Prediction)
                .join(EmailEvent, EmailEvent.id == Prediction.emailEventId)
                .where(
                    EmailEvent.userId == user_id,
                    Prediction.predictedLabel == "legitimate",
                )
            ) or 0

            phishing_ratio: float = (
                total_phishing / total_scanned if total_scanned > 0 else 0.0
            )

            # Daily buckets for the trend chart
            from datetime import date, timedelta  # local to avoid top-level import conflict
            today = date.today()
            daily_rows = session.execute(
                select(
                    func.date(EmailEvent.receivedAt).label("day"),
                    func.count(EmailEvent.id).label("total"),
                    func.sum(
                        func.iif(Prediction.predictedLabel == "phishing", 1, 0)
                    ).label("phishing_total"),
                )
                .outerjoin(Prediction, Prediction.emailEventId == EmailEvent.id)
                .where(
                    EmailEvent.userId == user_id,
                    func.date(EmailEvent.receivedAt) >= str(today - timedelta(days=trend_days - 1)),
                )
                .group_by(func.date(EmailEvent.receivedAt))
                .order_by(func.date(EmailEvent.receivedAt))
            ).all()

            # Build a full dense series (fill in 0s for missing days)
            row_map = {r.day: (r.total, int(r.phishing_total or 0)) for r in daily_rows}
            daily = []
            for i in range(trend_days):
                d = str(today - timedelta(days=trend_days - 1 - i))
                total, phish = row_map.get(d, (0, 0))
                daily.append({"date": d, "total": total, "phishing": phish})

            # Risk-level breakdown for the donut chart
            def _risk_count(level: str) -> int:
                return session.scalar(
                    select(func.count())
                    .select_from(Prediction)
                    .join(EmailEvent, EmailEvent.id == Prediction.emailEventId)
                    .where(
                        EmailEvent.userId == user_id,
                        Prediction.riskLevel == level,
                    )
                ) or 0

            risk_high = _risk_count("HIGH")
            risk_medium = _risk_count("MEDIUM")
            risk_low = _risk_count("LOW")
            risk_unscanned = total_scanned - (risk_high + risk_medium + risk_low)

            return {
                "total_scanned": total_scanned,
                "total_phishing": total_phishing,
                "total_legitimate": total_legitimate,
                "phishing_ratio": phishing_ratio,
                "risk_high": risk_high,
                "risk_medium": risk_medium,
                "risk_low": risk_low,
                "risk_unscanned": risk_unscanned,
                "daily_trend": daily,
            }

    def get_user_predictions(self, user_id, limit=100):
        with self._session_scope() as session:
            stmt = (
                select(EmailEvent, Prediction)
                .outerjoin(Prediction, EmailEvent.id == Prediction.emailEventId)
                .where(EmailEvent.userId == user_id)
                .order_by(EmailEvent.receivedAt.desc())
                .limit(limit)
            )
            results = session.execute(stmt).all()

            payload: List[Dict[str, object]] = []
            for event, prediction in results:
                payload.append(
                    {
                        "email_event_id": event.id,
                        "user_id": event.userId,
                        "sender_domain": event.senderDomain,
                        "is_forwarded": event.isForwarded,
                        "received_at": event.receivedAt,
                        "message_id_hash": event.messageIdHash,
                        "prediction": None
                        if not prediction
                        else {
                            "prediction_id": prediction.id,
                            "model_version": prediction.modelVersion,
                            "phishing_probability": prediction.phishingProbability,
                            "predicted_label": prediction.predictedLabel,
                            "risk_level": prediction.riskLevel,
                            "created_at": prediction.createdAt,
                        },
                    }
                )
            return payload

    def get_all_predictions(self, limit: int = 100) -> List[Dict[str, object]]:
        """Return scan history across ALL users (admin view).

        Each record includes ``user_email`` set to the stored email hash
        (no plain email is ever persisted).
        """
        with self._session_scope() as session:
            stmt = (
                select(User, EmailEvent, Prediction)
                .join(EmailEvent, EmailEvent.userId == User.id)
                .outerjoin(Prediction, Prediction.emailEventId == EmailEvent.id)
                .order_by(EmailEvent.receivedAt.desc())
                .limit(limit)
            )
            results = session.execute(stmt).all()

            payload: List[Dict[str, object]] = []
            for user, event, prediction in results:
                payload.append(
                    {
                        "email_event_id": event.id,
                        "user_id": event.userId,
                        "user_email": user.emailHash,  # hash only – no plain email stored
                        "sender_domain": event.senderDomain,
                        "is_forwarded": event.isForwarded,
                        "received_at": event.receivedAt,
                        "message_id_hash": event.messageIdHash,
                        "prediction": None
                        if not prediction
                        else {
                            "prediction_id": prediction.id,
                            "model_version": prediction.modelVersion,
                            "phishing_probability": prediction.phishingProbability,
                            "predicted_label": prediction.predictedLabel,
                            "risk_level": prediction.riskLevel,
                            "created_at": prediction.createdAt,
                        },
                    }
                )
            return payload

    def get_system_metrics(self) -> Dict[str, object]:
        """Return aggregate system-wide metrics for the admin dashboard."""
        with self._session_scope() as session:
            total_scanned: int = session.scalar(
                select(func.count()).select_from(EmailEvent)
            ) or 0

            total_phishing: int = session.scalar(
                select(func.count())
                .select_from(Prediction)
                .where(Prediction.predictedLabel == "phishing")
            ) or 0

            total_legitimate: int = session.scalar(
                select(func.count())
                .select_from(Prediction)
                .where(Prediction.predictedLabel == "legitimate")
            ) or 0

            phishing_ratio: float = (
                total_phishing / total_scanned if total_scanned > 0 else 0.0
            )

            # Top 10 sender domains by total volume
            domain_rows = session.execute(
                select(
                    EmailEvent.senderDomain,
                    func.count(EmailEvent.id).label("total"),
                    func.sum(
                        func.iif(Prediction.predictedLabel == "phishing", 1, 0)
                    ).label("phishing_total"),
                )
                .outerjoin(Prediction, Prediction.emailEventId == EmailEvent.id)
                .where(EmailEvent.senderDomain != "")
                .group_by(EmailEvent.senderDomain)
                .order_by(func.count(EmailEvent.id).desc())
                .limit(10)
            ).all()

            top_sender_domains = [
                {
                    "domain": row.senderDomain,
                    "count": row.total,
                    "phishing_count": int(row.phishing_total or 0),
                }
                for row in domain_rows
            ]

            return {
                "total_scanned": total_scanned,
                "total_phishing": total_phishing,
                "total_legitimate": total_legitimate,
                "phishing_ratio": phishing_ratio,
                "top_sender_domains": top_sender_domains,
            }
