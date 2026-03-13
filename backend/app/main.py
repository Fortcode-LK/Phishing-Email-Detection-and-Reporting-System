"""FastAPI web API for the Phishing Detection System.

Run from the backend/app/ directory:
    uvicorn main:app --reload --port 8000
"""
from __future__ import annotations

import hashlib
import logging
import sys
from pathlib import Path

from datetime import datetime, timezone
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("phishing_shield")

# ── Resolve paths so imports and DB work from any CWD ────────────────────────
_APP_DIR = Path(__file__).parent.resolve()
_REPO_ROOT = _APP_DIR.parent.parent  # phishing-project/phishing-project/
sys.path.insert(0, str(_APP_DIR))

# Patch DATABASE_URL before DatabaseManager is imported so SQLite resolves
# to the single shared DB at the repo root.
import database as _db_module  # noqa: E402
_db_module.DATABASE_URL = f"sqlite:///{_REPO_ROOT / 'phishing_detector.db'}"

from auth import create_token, get_current_user  # noqa: E402
from database import DatabaseManager  # noqa: E402
from schemas import (  # noqa: E402
    AddWhitelistRequest,
    AdminMetricsOut,
    AdminScanRecordOut,
    EmailAlertsOut,
    EmailAlertsUpdate,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    ScanRecordOut,
    UserOut,
    UserSummaryOut,
    WhitelistItem,
)

# ── App + CORS ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Phishing Shield API",
    version="1.0.0",
    description="REST API for the Phishing Detection MVP",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Singleton DB manager ───────────────────────────────────────────────────────
db = DatabaseManager()

# Seed the single admin account (username: Admin, password: Admin).
# Uses the same lowercase SHA-256 hashing the login endpoint applies.
db.ensure_admin_user(
    email_hash=hashlib.sha256("admin".encode("utf-8")).hexdigest(),
    password_hash=hashlib.sha256("admin".encode("utf-8")).hexdigest(),
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(">>> %s %s", request.method, request.url.path)
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled exception during %s %s", request.method, request.url.path)
        raise
    status = response.status_code
    level = logging.WARNING if status >= 400 else logging.INFO
    logger.log(level, "<<< %s %s → %d", request.method, request.url.path, status)
    return response

# ── Helpers ───────────────────────────────────────────────────────────────────

def _sha256(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode("utf-8")).hexdigest()


# ── Auth routes ──────────────────────────────────────────────────────────────

@app.post("/api/login", response_model=LoginResponse)
def login(body: LoginRequest):
    """Authenticate a user and return a JWT."""
    email_hash = _sha256(body.email)
    password_hash = _sha256(body.password)

    user = db.get_user_by_email_hash(email_hash)
    if not user or user.passwordHash != password_hash:
        raise HTTPException(
            status_code=401,
            detail={"error": "Invalid credentials"},
        )

    token = create_token(user_id=user.id, email=body.email, role=user.role)
    return LoginResponse(
        token=token,
        user=UserOut(id=user.id, email=body.email),
    )


@app.get("/api/me", response_model=UserOut)
def me(current_user: dict = Depends(get_current_user)):
    """Return the authenticated user's basic info."""
    return UserOut(id=current_user["user_id"], email=current_user["email"])


# ── Registration ──────────────────────────────────────────────────────────────

@app.post("/api/register", response_model=RegisterResponse, status_code=201)
def register(body: RegisterRequest):
    """Register a new user account."""
    logger.debug("Register attempt — email=%s", body.email)
    email_hash = _sha256(body.email)
    password_hash = _sha256(body.password)

    try:
        user = db.create_user(
            email_hash=email_hash,
            password_hash=password_hash,
            first_name=body.firstName or None,
            last_name=body.lastName or None,
            mobile_number=body.mobileNumber or None,
            address=body.address or None,
        )
    except ValueError as exc:
        msg = str(exc).lower()
        logger.warning("Register ValueError for email=%s: %s", body.email, exc)
        if "already exists" in msg:
            raise HTTPException(
                status_code=409,
                detail={"error": "User with this email already exists"},
            )
        raise HTTPException(status_code=400, detail={"error": str(exc)})
    except Exception as exc:
        logger.exception("Unexpected error during registration for email=%s", body.email)
        raise HTTPException(
            status_code=500, detail={"error": "Internal server error"}
        ) from exc

    logger.info("User registered successfully — id=%d email=%s", user.id, body.email)
    return RegisterResponse(id=user.id, email=body.email)


# ── User routes (protected) ──────────────────────────────────────────────────

@app.get("/api/predictions", response_model=list[ScanRecordOut])
def get_predictions(
    limit: int = Query(default=50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """Return scan history for the authenticated user.

    Trusted domains are returned with a synthetic 'legitimate / 0.0'
    prediction so the UI always shows them as safe.
    """
    try:
        records = db.get_user_predictions(current_user["user_id"], limit=limit)
    except Exception as exc:
        logger.exception("Error fetching predictions for user_id=%s", current_user["user_id"])
        raise HTTPException(
            status_code=500, detail={"error": "Internal server error"}
        ) from exc

    # Override prediction for trusted domains
    now_iso = datetime.now(tz=timezone.utc)
    for rec in records:
        if db.is_trusted_domain(current_user["user_id"], rec["sender_domain"]):
            rec["prediction"] = {
                "prediction_id": None,
                "model_version": "trusted_domain",
                "phishing_probability": 0.0,
                "predicted_label": "legitimate",
                "risk_level": "LOW",
                "created_at": now_iso,
            }

    return records


@app.get("/api/user/summary", response_model=UserSummaryOut)
def get_user_summary(
    trend_days: int = Query(default=14, ge=7, le=90),
    current_user: dict = Depends(get_current_user),
):
    """Return accurate per-user aggregate stats and daily trend data."""
    try:
        summary = db.get_user_summary(current_user["user_id"], trend_days=trend_days)
    except Exception as exc:
        logger.exception("Error fetching summary for user_id=%s", current_user["user_id"])
        raise HTTPException(
            status_code=500, detail={"error": "Internal server error"}
        ) from exc
    return summary


# ── Whitelist routes (protected) ─────────────────────────────────────────────
@app.get("/api/user/alerts", response_model=EmailAlertsOut)
def get_email_alerts(current_user: dict = Depends(get_current_user)):
    """Return the current user's email alert preference."""
    enabled = db.get_email_alerts_enabled(current_user["user_id"])
    return EmailAlertsOut(email_alerts_enabled=enabled)


@app.put("/api/user/alerts", response_model=EmailAlertsOut)
def set_email_alerts(body: EmailAlertsUpdate, current_user: dict = Depends(get_current_user)):
    """Enable or disable email scan-result alerts for the current user."""
    try:
        enabled = db.set_email_alerts_enabled(current_user["user_id"], body.email_alerts_enabled)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail={"error": str(exc)})
    logger.info("Email alerts %s for user_id=%d", "enabled" if enabled else "disabled", current_user["user_id"])
    return EmailAlertsOut(email_alerts_enabled=enabled)


# ── Whitelist routes (protected) ───────────────────────────────────────────────
@app.get("/api/whitelist", response_model=list[WhitelistItem])
def get_whitelist(current_user: dict = Depends(get_current_user)):
    """Return the current user's trusted domains."""
    return db.get_user_trusted_domains(current_user["user_id"])


@app.post("/api/whitelist", response_model=WhitelistItem, status_code=201)
def add_whitelist(body: AddWhitelistRequest, current_user: dict = Depends(get_current_user)):
    """Add a domain to the current user's whitelist."""
    entry = db.add_trusted_domain(
        user_id=current_user["user_id"],
        domain=body.domain.lower().strip(),
        reason=body.reason or "",
    )
    # Refresh to get the created_at stamp
    domains = db.get_user_trusted_domains(current_user["user_id"])
    for d in domains:
        if d["domain"] == body.domain.lower().strip():
            return d
    return {"id": entry.id, "domain": entry.domain, "reason": entry.reason or "", "created_at": entry.createdAt}


@app.delete("/api/whitelist/{domain:path}", status_code=204)
def remove_whitelist(domain: str, current_user: dict = Depends(get_current_user)):
    """Remove a domain from the current user's whitelist."""
    deleted = db.remove_trusted_domain(current_user["user_id"], domain)
    if not deleted:
        raise HTTPException(status_code=404, detail={"error": "Domain not found in whitelist"})
    return Response(status_code=204)


# ── Admin routes (protected) ─────────────────────────────────────────────────

@app.get("/api/admin/predictions", response_model=list[AdminScanRecordOut])
def get_admin_predictions(
    limit: int = Query(default=100, ge=1, le=500),
    current_user: dict = Depends(get_current_user),
):
    """Return system-wide scan history across all users (admin)."""
    try:
        records = db.get_all_predictions(limit=limit)
    except Exception as exc:
        logger.exception("Error fetching admin predictions")
        raise HTTPException(
            status_code=500, detail={"error": "Internal server error"}
        ) from exc

    return records


@app.get("/api/admin/metrics", response_model=AdminMetricsOut)
def get_admin_metrics(current_user: dict = Depends(get_current_user)):
    """Return global aggregate metrics for the admin dashboard."""
    try:
        metrics = db.get_system_metrics()
    except Exception as exc:
        logger.exception("Error fetching admin metrics")
        raise HTTPException(
            status_code=500, detail={"error": "Internal server error"}
        ) from exc

    return metrics


# ── Health check ───────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok"}
