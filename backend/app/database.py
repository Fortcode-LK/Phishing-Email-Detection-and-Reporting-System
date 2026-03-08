"""SQLite-backed database utilities for the phishing detector."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Dict, List

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from models import Base, EmailEvent, Prediction, TrustedDomain, User

DATABASE_URL = "sqlite:///phishing_detector.db"


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
        self._Session = sessionmaker(
            bind=self.engine,
            future=True,
            expire_on_commit=False,
        )

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
            return user

    def get_user_by_email_hash(self, email_hash):
        with self._session_scope() as session:
            return session.scalar(select(User).where(User.emailHash == email_hash))

    def log_email_event(self, user_id, sender_domain, is_forwarded=False, message_id_hash=None):
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
                raise ValueError("Prediction already exists for this EmailEvent")

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
