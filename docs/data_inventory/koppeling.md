# Koppeling tussen bronnen

Automatisch gemaakt door `pipeline/linkage_report.py` bij elke run. Sleutels: `location_key` (AGB organisatie + postcode) voor locaties, kwaliteit en wachttijden; AGB organisatie voor contracten.

## Locaties (Zorginzicht)

- 371 locaties van 195 organisaties
- met coördinaten: 353/371 (95%)

## Kwaliteit (metingen)

- 59,684 metingen, gekoppeld aan een locatie: 59,684/59,684 (100%)

Aantal locaties met metingen per ingreep en verslagjaar:

| ingreep | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| heup | 85 | 88 | 88 | 89 |
| knie | 86 | 87 | 87 | 89 |
| staar | 100 | 102 | 88 | 110 |

## Contracten

- ziekenhuizen in `hospitals.csv` met AGB die ook in Zorginzicht staat: 9/9 (100%)
- organisaties in Zorginzicht zonder contractbron in `hospitals.csv`: 186
- contractkandidaten (nog te controleren): 664
- gecontroleerde contracten: 0

## Wachttijden (NZa)

Nog geen data (zie docs/bronnen.md).

## Integriteit (DuckDB)

| controle | aantal |
|---|---|
| measurement without location | ✅ 0 |
| measurement without indicator | ✅ 0 |
| location without coordinates | ⚠️ 18 |
| duplicate location_key | ✅ 0 |
| manual hospital AGB not in Zorginzicht | ✅ 0 |

