"""Launch phishing-project services in separate PowerShell terminals.

Services started:
1. Backend API (FastAPI / uvicorn)
2. Frontend (Vite)
3. Model pipeline (SMTP scanner)
4. Gmail forwarder helper

Usage:
    python start_services.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

SERVICES: list[tuple[str, Path, str]] = [
    (
        "Backend API",
        PROJECT_ROOT / "backend" / "app",
        "uvicorn main:app --host 0.0.0.0 --port 8000 --reload",
    ),
    (
        "Frontend",
        PROJECT_ROOT / "frontend",
        "npm run dev",
    ),
    (
        "Model SMTP Server",
        PROJECT_ROOT / "backend" / "app",
            "python smtp_server.py --reply",
    ),
    (
        "Gmail Forwarder",
        PROJECT_ROOT / "tools",
        "python gmail_forwarder.py",
    ),
]


def _build_ps_command(cwd: Path, command: str) -> str:
    return (
        f"$Host.UI.RawUI.WindowTitle = 'Phishing Shield - {command}'; "
        f"Set-Location -Path '{cwd}'; "
        f"{command}"
    )


def _open_in_new_powershell(cwd: Path, command: str) -> subprocess.Popen[bytes]:
    ps_command = _build_ps_command(cwd, command)
    return subprocess.Popen(
        [
            "powershell",
            "-NoExit",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            ps_command,
        ],
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )


def main() -> int:
    if sys.platform != "win32":
        print("This launcher is intended for Windows (PowerShell).")
        return 1

    print("Launching services in separate terminals...")
    for name, cwd, command in SERVICES:
        if not cwd.exists():
            print(f"[SKIP] {name}: missing folder {cwd}")
            continue

        _open_in_new_powershell(cwd, command)
        print(f"[OK] {name}: {command}")

    print("Done. Four terminals should now be opening.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
