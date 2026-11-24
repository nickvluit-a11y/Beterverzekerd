"""Read unknown spreadsheets/CSVs, describe them, and find columns by name."""

from __future__ import annotations

import io
import re
import sys
import zipfile
from pathlib import Path

import pandas as pd

DATA_SUFFIXES = {".csv", ".xlsx", ".xls"}


def read_any(path: Path) -> dict[str, pd.DataFrame]:
    """All tables in a csv/xlsx/xls/zip file as {name: DataFrame}, everything as text.

    Unreadable files or zip members are reported on stderr and skipped.
    """
    suffix = path.suffix.lower()
    if suffix == ".zip":
        tables: dict[str, pd.DataFrame] = {}
        try:
            archive = zipfile.ZipFile(path)
        except zipfile.BadZipFile as exc:
            print(f"skip {path.name}: {exc}", file=sys.stderr)
            return {}
        with archive:
            for member in archive.namelist():
                inner = Path(member)
                if member.startswith("__MACOSX/") or inner.name.startswith("._"):
                    continue
                if inner.suffix.lower() in DATA_SUFFIXES:
                    for name, df in _read_bytes(archive.read(member), inner.suffix.lower(), member).items():
                        tables[f"{inner.name}:{name}"] = df
        return tables
    return _read_bytes(path.read_bytes(), suffix, path.name)


def decode(data: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1")  # never fails


def _read_bytes(data: bytes, suffix: str, label: str) -> dict[str, pd.DataFrame]:
    try:
        if suffix in {".xlsx", ".xls"}:
            return pd.read_excel(io.BytesIO(data), sheet_name=None, dtype=str)
        if suffix == ".csv":
            text = decode(data)
            first = text.splitlines()[0] if text.strip() else ""
            if not first:
                return {}
            sep = ";" if first.count(";") > first.count(",") else ","
            return {"csv": pd.read_csv(io.StringIO(text), sep=sep, dtype=str)}
    except Exception as exc:  # one bad file must not stop the run
        print(f"skip {label}: {type(exc).__name__}: {exc}", file=sys.stderr)
    return {}


def find_column(df: pd.DataFrame, *patterns: str, exclude: str | None = None, required: bool = True) -> str | None:
    """First column whose lowercased name matches a regex in `patterns` (tried in order of patterns),
    skipping names that match `exclude`."""
    for pattern in patterns:
        for column in df.columns:
            name = str(column).lower()
            if exclude and re.search(exclude, name):
                continue
            if re.search(pattern, name):
                return column
    if required:
        raise KeyError(f"No column matching {patterns}; columns are: {list(df.columns)}")
    return None


def describe(tables: dict[str, pd.DataFrame], title: str, highlight: str | None = None, max_values: int = 40) -> str:
    """Markdown description: columns, row counts, sample rows, and values matching `highlight`."""
    lines = [f"# {title}", ""]
    for name, df in tables.items():
        lines += [f"## {name}", "", f"{len(df):,} rows × {len(df.columns)} columns", "", "Columns:", ""]
        lines += [f"- `{c}`" for c in df.columns]
        lines += ["", "First rows:", "", "```", df.head(5).to_string(max_colwidth=40), "```", ""]
        if highlight:
            regex = re.compile(highlight, re.IGNORECASE)
            for column in df.columns:
                values = df[column].dropna().astype(str).unique()
                hits = [v for v in values if regex.search(v)]
                if hits and len(values) < 5000:
                    lines += [f"Values in `{column}` matching `{highlight}` ({len(hits)}):", ""]
                    lines += [f"- {v}" for v in sorted(hits)[:max_values]]
                    lines.append("")
    return "\n".join(lines)
