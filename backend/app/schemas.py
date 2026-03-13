"""Pydantic request/response schemas for the phishing detection API."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ── Authentication ────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str        # accepts plain username or email address
    password: str


class UserOut(BaseModel):
    id: int
    email: str


class LoginResponse(BaseModel):
    token: str
    user: UserOut


# ── Registration ──────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    firstName: Optional[str] = Field(None, max_length=50)
    lastName: Optional[str] = Field(None, max_length=50)
    mobileNumber: Optional[str] = Field(None, pattern=r"^[+\d]{8,15}$")
    address: Optional[str] = Field(None, max_length=200)


class RegisterResponse(BaseModel):
    id: int
    email: str

# ── User summary (/api/user/summary) ─────────────────────────────────────────

class DailyTrendPoint(BaseModel):
    date: str          # YYYY-MM-DD
    total: int
    phishing: int


class UserSummaryOut(BaseModel):
    total_scanned: int
    total_phishing: int
    total_legitimate: int
    phishing_ratio: float
    risk_high: int
    risk_medium: int
    risk_low: int
    risk_unscanned: int
    daily_trend: list[DailyTrendPoint]

# ── Whitelist ────────────────────────────────────────────────────────────────

class AddWhitelistRequest(BaseModel):
    domain: str = Field(..., min_length=3, max_length=253, pattern=r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$")
    reason: Optional[str] = Field("", max_length=300)


class WhitelistItem(BaseModel):
    id: int
    domain: str
    reason: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Shared prediction ─────────────────────────────────────────────────────────

class PredictionOut(BaseModel):
    prediction_id: Optional[int]  # None for trusted-domain synthetic predictions
    model_version: str
    phishing_probability: float
    predicted_label: str
    risk_level: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── User scan history (/api/predictions) ──────────────────────────────────────

class ScanRecordOut(BaseModel):
    email_event_id: int
    user_id: int
    sender_domain: str
    is_forwarded: bool
    received_at: datetime
    message_id_hash: Optional[str]
    prediction: Optional[PredictionOut]

    model_config = {"from_attributes": True}


# ── Admin scan history (/api/admin/predictions) ───────────────────────────────

class AdminScanRecordOut(ScanRecordOut):
    user_email: str  # stores the email hash (no plain email in DB)


# ── Admin metrics (/api/admin/metrics) ────────────────────────────────────────

class TopSenderDomain(BaseModel):
    domain: str
    count: int
    phishing_count: int


class AdminMetricsOut(BaseModel):
    total_scanned: int
    total_phishing: int
    total_legitimate: int
    phishing_ratio: float
    top_sender_domains: list[TopSenderDomain]


# ── Email alerts (/api/user/alerts) ───────────────────────────────────────────

class EmailAlertsOut(BaseModel):
    email_alerts_enabled: bool


class EmailAlertsUpdate(BaseModel):
    email_alerts_enabled: bool
