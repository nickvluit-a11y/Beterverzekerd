# Beterverzekerd

Compare Dutch health insurance policies on the quality of the care they contract — not just on price.

Beterverzekerd links four layers that are public today but never combined:
contract status per hospital × insurer/policy, hospital quality and volume indicators (Zorginzicht),
waiting times (NZa), and aggregate review scores — plus premiums.

Status: idea / scaffolding. See `CLAUDE.md` for full context and `docs/` for details.

## Structure
- `scrapers/` — one fetcher per source, writes to `data/raw/<source>/<date>/`
- `pipeline/` — normalise and link everything (AGB code, label → concern → policy)
- `data/` — raw and processed data
- `app/` — the comparison front-end
- `.github/workflows/` — scheduled scraping runs
