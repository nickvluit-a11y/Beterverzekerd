"""Read unknown spreadsheets/CSVs, describe them, and find columns by name."""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

import pandas as pd


def read_any(path: Path) -> dict[str, pd.DataFrame]:
    """All tables in a csv/xlsx/zip file as {name: DataFrame}. Everything is read as text."""
    suffix = path.suffix.lower()
    if suffix == ".zip":
        tables: dict[str, pd.DataFrame] = {}
        with zipfile.ZipFile(path) as archive:
            for member in archive.namelist():
                if Path(member).suffix.lower() in {".csv", ".xlsx", ".xls"}:
                    inner = Path(member)
                    data = archive.read(member)
                    for name, df in _read_bytes(data, inner.suffix.lower()).items():
                        tables[f"{inner.name}:{name}"] = df
        return tables
    return _read_bytes(path.read_bytes(), suffix)


def _read_bytes(data: bytes, suffix: str) -> dict[str, pd.DataFrame]:
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(io.BytesIO(data), sheet_name=None, dtype=str)
    if suffix == ".csv":
        for encoding in ("utf-8-sig", "cp1252"):
            try:
                text = data.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        sep = ";" if text.splitlines()[0].count(";") > text.splitlines()[0].count(",") else ","
        return {"csv": pd.read_csv(io.StringIO(text), sep=sep, dtype=str)}
    return {}


def find_column(df: pd.DataFrame, *patterns: str, required: bool = True) -> str | None:
    """First column whose (lowercased) name matches any regex in `patterns`, tried in order."""
    for pattern in patterns:
        for column in df.columns:
            if re.search(pattern, str(column).lower()):
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
