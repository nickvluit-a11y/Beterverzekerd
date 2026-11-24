# Beterverzekerd

Compare Dutch health insurance policies on the quality of the care they contract — not just on price.

Beterverzekerd links three layers that are public today but never combined:
contract status per hospital × insurer/policy, hospital quality and volume indicators (Zorginzicht),
waiting times (NZa) — plus premiums. Data comes directly from the organisations that produce it, not from comparison platforms.

Status: working prototype on a small hospital list (around Utrecht). See `CLAUDE.md` for full context
and `docs/bronnen.md` for the data sources.

## Structure
- `scrapers/` — one fetcher per source, writes to `data/raw/<source>/<date>/` (not committed; kept as workflow artifact)
  - `zorginzicht.py` — Zorginzicht MSZ open data (Excel)
  - `nza_wachttijden.py` — NZa waiting-times CSV
  - `contracts.py` — contract overviews hospitals publish, PDF or web page (`contracts_url` in `hospitals.csv`)
  - `check_sources.py` — reachability + robots.txt report for every source
- `pipeline/` — normalise and link everything
  - `reference.py` — hospital and label matching (aliases, fuzzy)
  - `zorginzicht_ingest.py`, `nza_ingest.py`, `contracts_parse.py` — raw → `data/processed/`
  - `score.py` — per-policy overview (counts, no single ranking)
- `data/manual/` — hand-maintained reference tables (see `data/manual/README.md`)
- `data/processed/` — pipeline output, committed by the `fetch-data` workflow
- `docs/data_inventory/` — column descriptions of the real source files, written by the pipeline
- `app/app.py` — Streamlit prototype
- `.github/workflows/` — `fetch-data` (Mon/Thu), `check-sources` (weekly), `tests` (every push)

## Running locally
```
pip install -r requirements.txt
python -m pytest
streamlit run app/app.py
```
