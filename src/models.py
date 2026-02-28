"""SQLAlchemy ORM models for the phishing detector database."""
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    __tablename__ = "User"

    id = Column(Integer, primary_key=True)
    emailHash = Column(String, unique=True, nullable=False)
    passwordHash = Column(String, nullable=False)
    role = Column(String, default="normal")
    firstName = Column(String)
    lastName = Column(String)
    mobileNumber = Column(String, unique=True)
    address = Column(String)
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())

    emailEvents = relationship("EmailEvent", back_populates="user")
    trustedDomains = relationship("TrustedDomain", back_populates="user")


class EmailEvent(Base):
    __tablename__ = "EmailEvent"

    id = Column(Integer, primary_key=True)
    userId = Column(Integer, ForeignKey("User.id"))
    senderDomain = Column(String, nullable=False)
    isForwarded = Column(Boolean, default=False)
    receivedAt = Column(DateTime, default=func.now())
    messageIdHash = Column(String, unique=True)

    user = relationship("User", back_populates="emailEvents")
    prediction = relationship("Prediction", back_populates="emailEvent", uselist=False)


class Prediction(Base):
    __tablename__ = "Prediction"

    id = Column(Integer, primary_key=True)
    emailEventId = Column(Integer, ForeignKey("EmailEvent.id"), unique=True)
    modelVersion = Column(String, nullable=False)
    phishingProbability = Column(Float, nullable=False)
    predictedLabel = Column(String, nullable=False)
    riskLevel = Column(String, nullable=False)
    createdAt = Column(DateTime, default=func.now())

    emailEvent = relationship("EmailEvent", back_populates="prediction")


class TrustedDomain(Base):
    __tablename__ = "TrustedDomain"

    id = Column(Integer, primary_key=True)
    userId = Column(Integer, ForeignKey("User.id"))
    domain = Column(String, nullable=False)
    reason = Column(String)
    createdAt = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="trustedDomains")

    __table_args__ = (UniqueConstraint("userId", "domain"),)
