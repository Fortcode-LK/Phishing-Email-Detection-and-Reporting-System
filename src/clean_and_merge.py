"""
clean_and_merge.py
==================
Cleans, standardises and merges multiple email datasets into one balanced
CSV file (10 000 rows, 50/50 phishing vs. legitimate) for downstream
phishing-detection modelling.

Author : Senior Data Engineer
Date   : 2026-02-20
"""

import csv
import os
import re
import warnings

import pandas as pd

warnings.filterwarnings("ignore")

# ── paths ────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
OUT_PATH = os.path.join(BASE_DIR, "data", "final_cleaned_dataset.csv")


# ═══════════════════════════════════════════════════════════════════════
# STEP 1 – Cleaning Function
# ═══════════════════════════════════════════════════════════════════════

def clean_email_text(text: object) -> str:
    """Clean a single text value (subject or body) for safe CSV export.

    1. Convert NaN / non-string → empty string.
    2. Strip HTML tags & entities.
    3. Replace \\n, \\r, \\t with a single space (prevents row-breaking).
    4. Collapse multiple spaces and strip edges.
    5. Escape internal double-quotes by doubling them (" → "").
    """
    # 1 – handle missing / non-string
    if not isinstance(text, str):
        return ""

    # 2 – remove HTML tags and decode common HTML entities
    text = re.sub(r"<[^>]+>", " ", text)                       # strip tags
    text = re.sub(r"&nbsp;", " ", text, flags=re.IGNORECASE)   # non-breaking space
    text = re.sub(r"&amp;", "&", text, flags=re.IGNORECASE)
    text = re.sub(r"&lt;", "<", text, flags=re.IGNORECASE)
    text = re.sub(r"&gt;", ">", text, flags=re.IGNORECASE)
    text = re.sub(r"&quot;", '"', text, flags=re.IGNORECASE)
    text = re.sub(r"&#\d+;", " ", text)                        # numeric entities
    text = re.sub(r"&\w+;", " ", text)                         # remaining entities

    # 3 – normalise whitespace characters that break CSV rows
    text = text.replace("\r\n", " ").replace("\r", " ").replace("\n", " ").replace("\t", " ")

    # 4 – collapse multiple spaces
    text = re.sub(r" {2,}", " ", text).strip()

    # 5 – double any embedded double-quotes so they survive QUOTE_ALL
    text = text.replace('"', '""')

    return text


# ═══════════════════════════════════════════════════════════════════════
# STEP 2 – Load & Map Each Dataset to the Standard Schema
# ═══════════════════════════════════════════════════════════════════════
# Target columns: subject, body, has_urls (0/1), label (1=Phishing, 0=Legit), source_dataset

def _read(filename: str, **kwargs) -> pd.DataFrame:
    """Try UTF-8 first, fall back to latin-1."""
    path = os.path.join(RAW_DIR, filename)
    try:
        return pd.read_csv(path, on_bad_lines="skip", encoding="utf-8", **kwargs)
    except (UnicodeDecodeError, Exception):
        return pd.read_csv(path, on_bad_lines="skip", encoding="latin-1", **kwargs)


def load_phishtank() -> pd.DataFrame:
    """PhishTank – all phishing, all have URLs."""
    df = _read("verified_online_PhishTank.csv")
    return pd.DataFrame({
        "subject": "",
        "body": df["url"].astype(str),
        "has_urls": 1,
        "label": 1,
        "source_dataset": "PhishTank",
    })


def load_ceas08() -> pd.DataFrame:
    df = _read("CEAS_08.csv")
    return pd.DataFrame({
        "subject": df["subject"],
        "body": df["body"],
        "has_urls": df["urls"].apply(lambda x: 1 if x else 0),
        "label": df["label"],
        "source_dataset": "CEAS_08",
    })


def load_nazario() -> pd.DataFrame:
    df = _read("Nazario.csv")
    return pd.DataFrame({
        "subject": df["subject"],
        "body": df["body"],
        "has_urls": df["urls"].apply(lambda x: 1 if x else 0),
        "label": df["label"],
        "source_dataset": "Nazario",
    })


def load_spamassasin() -> pd.DataFrame:
    df = _read("SpamAssasin.csv")
    return pd.DataFrame({
        "subject": df["subject"],
        "body": df["body"],
        "has_urls": df["urls"].apply(lambda x: 1 if x else 0),
        "label": df["label"],
        "source_dataset": "SpamAssasin",
    })


def load_nigerian_fraud() -> pd.DataFrame:
    df = _read("Nigerian_Fraud.csv")
    return pd.DataFrame({
        "subject": df["subject"],
        "body": df["body"],
        "has_urls": df["urls"].apply(lambda x: 1 if x else 0),
        "label": df["label"],
        "source_dataset": "Nigerian_Fraud",
    })


def load_enron() -> pd.DataFrame:
    df = _read("Enron.csv")
    return pd.DataFrame({
        "subject": df["subject"],
        "body": df["body"],
        "has_urls": 0,
        "label": df["label"],
        "source_dataset": "Enron",
    })


def load_ling() -> pd.DataFrame:
    df = _read("Ling.csv")
    return pd.DataFrame({
        "subject": df["subject"],
        "body": df["body"],
        "has_urls": 0,
        "label": df["label"],
        "source_dataset": "Ling",
    })


def load_phishing_email() -> pd.DataFrame:
    df = _read("phishing_email.csv")
    return pd.DataFrame({
        "subject": "",
        "body": df["text_combined"],
        "has_urls": 0,
        "label": df["label"],
        "source_dataset": "phishing_email",
    })


# ═══════════════════════════════════════════════════════════════════════
# STEP 3 & 4 – Merge, Clean, Deduplicate, Balance, and Export
# ═══════════════════════════════════════════════════════════════════════

def main() -> None:
    print("=" * 60)
    print("  Phishing Detection – Data Cleaning & Merging Pipeline")
    print("=" * 60)

    # ── load all datasets ────────────────────────────────────────────
    loaders = [
        ("PhishTank",       load_phishtank),
        ("CEAS_08",         load_ceas08),
        ("Nazario",         load_nazario),
        ("SpamAssasin",     load_spamassasin),
        ("Nigerian_Fraud",  load_nigerian_fraud),
        ("Enron",           load_enron),
        ("Ling",            load_ling),
        ("phishing_email",  load_phishing_email),
    ]

    frames = []
    for name, loader in loaders:
        df = loader()
        print(f"  [+] Loaded {name:20s} → {len(df):>6,} rows")
        frames.append(df)

    merged = pd.concat(frames, ignore_index=True)
    print(f"\n  Total merged rows: {len(merged):,}")

    # ── apply cleaning to subject & body ─────────────────────────────
    print("\n  Cleaning subject & body columns …")
    merged["subject"] = merged["subject"].apply(clean_email_text)
    merged["body"]    = merged["body"].apply(clean_email_text)
    print("  ✓ Cleaning complete.")

    # ── ensure has_urls is int 0/1 ───────────────────────────────────
    merged["has_urls"] = merged["has_urls"].astype(int)
    merged["label"]    = merged["label"].astype(int)

    # ── deduplicate on body ──────────────────────────────────────────
    before = len(merged)
    merged.drop_duplicates(subset=["body"], keep="first", inplace=True)
    merged.reset_index(drop=True, inplace=True)
    print(f"\n  Deduplication: {before:,} → {len(merged):,}  "
          f"(removed {before - len(merged):,} duplicates)")

    # ── label distribution before sampling ───────────────────────────
    print(f"\n  Label distribution after dedup:")
    for lbl in sorted(merged["label"].unique()):
        tag = "Phishing" if lbl == 1 else "Legitimate"
        print(f"    label={lbl} ({tag:>10s}): {(merged['label'] == lbl).sum():>6,}")

    # ── balanced sampling: 5 000 phishing + 5 000 legitimate ─────────
    SAMPLE_PER_CLASS = 5_000
    phishing   = merged[merged["label"] == 1]
    legitimate = merged[merged["label"] == 0]

    if len(phishing) < SAMPLE_PER_CLASS:
        raise ValueError(
            f"Not enough phishing rows ({len(phishing)}) to sample {SAMPLE_PER_CLASS}."
        )
    if len(legitimate) < SAMPLE_PER_CLASS:
        raise ValueError(
            f"Not enough legitimate rows ({len(legitimate)}) to sample {SAMPLE_PER_CLASS}."
        )

    phishing_sample   = phishing.sample(n=SAMPLE_PER_CLASS, random_state=42)
    legitimate_sample  = legitimate.sample(n=SAMPLE_PER_CLASS, random_state=42)

    final = pd.concat([phishing_sample, legitimate_sample], ignore_index=True)
    # shuffle so classes aren't contiguous
    final = final.sample(frac=1, random_state=42).reset_index(drop=True)

    print(f"\n  Final dataset : {len(final):,} rows  "
          f"(Phishing={len(final[final['label']==1]):,}, "
          f"Legitimate={len(final[final['label']==0]):,})")

    # ── fill any remaining NaN with empty strings for clean CSV ─────
    final.fillna("", inplace=True)

    # ── safe export ──────────────────────────────────────────────────
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    final.to_csv(
        OUT_PATH,
        index=False,
        quoting=csv.QUOTE_ALL,
        encoding="utf-8",
    )

    print(f"\n  ✓ Saved → {OUT_PATH}")
    print(f"  Columns : {list(final.columns)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
