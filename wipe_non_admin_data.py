"""Wipe all non-admin users and related data from project databases.

Keeps admin credentials intact where admin rows exist.

Usage:
    python wipe_non_admin_data.py
"""

from __future__ import annotations

import pathlib
import sqlite3

DBS = [
    pathlib.Path(__file__).resolve().parent / "phishing_detector.db",
    pathlib.Path(__file__).resolve().parent / "reply_test.db",
    pathlib.Path(__file__).resolve().parent / "backend" / "app" / "phishing_detector.db",
]


def main() -> int:
    for db_path in DBS:
        if not db_path.exists():
            print(f"SKIP (not found): {db_path}")
            continue

        con = sqlite3.connect(str(db_path))
        cur = con.cursor()

        tables = {
            row[0]
            for row in cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }

        print(f"\n--- {db_path.name}")
        print(f"Tables: {sorted(tables)}")

        deleted: dict[str, int] = {}

        if "Prediction" in tables:
            cur.execute("DELETE FROM Prediction")
            deleted["Prediction"] = cur.rowcount

        if "EmailEvent" in tables:
            cur.execute("DELETE FROM EmailEvent")
            deleted["EmailEvent"] = cur.rowcount

        if "TrustedDomain" in tables and "User" in tables:
            cur.execute(
                'DELETE FROM TrustedDomain WHERE userId IN (SELECT id FROM "User" WHERE role != \'admin\')'
            )
            deleted["TrustedDomain"] = cur.rowcount

        if "User" in tables:
            cur.execute('DELETE FROM "User" WHERE role != \'admin\'')
            deleted["User"] = cur.rowcount
            admins = cur.execute(
                'SELECT id, role FROM "User" WHERE role = \'admin\''
            ).fetchall()
            print(f"Admin rows remaining: {admins}")

        con.commit()
        con.close()

        print(f"Deleted rows: {deleted}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
