# Bronnen

Status per databron voor de MVP (heupprothese, knieprothese, staaroperatie).
Laatste deskcheck: 2026-11-24.

**Uitgangspunt: directe bronnen, geen platforms.** We halen data bij de partij die haar maakt of beheert
(Zorginstituut, NZa, Vektis, PDOK, ziekenhuizen, verzekeraars). Vergelijkers en doorgeefluiken
(Zorgkiezer, Zorgwijzer, Independer, Consumentenbond, ZorgkaartNederland, Apify e.d.) gebruiken we niet als bron;
hooguit om onze eigen uitkomst met de hand te controleren.

**Hoe is dit gecontroleerd?** De cloud-sandbox van Claude kan niet bij Nederlandse zorgsites (netwerk-allowlist).
Deze ronde is daarom alleen op basis van zoekresultaten gedaan. Elke URL heeft een markering:

- ✅ **bevestigd**: gevonden in zoekresultaten die de pagina zelf citeren
- 🟡 **waarschijnlijk**: sterke aanwijzing, exacte URL/formaat nog bevestigen
- ❓ **onbekend**: nog niet gevonden

De GitHub Action `check-sources` (zie `scrapers/check_sources.py`) haalt elke URL uit
`scrapers/sources.json` op vanaf het netwerk van GitHub, checkt `robots.txt` en schrijft een rapport naar
`docs/source_check/<datum>/report.md`. Draai die één keer om 🟡 om te zetten in ✅ of ❌.

---

## 1. Kwaliteitsindicatoren: Zorginzicht openbare data (Zorginstituut Nederland)

| | |
|---|---|
| Landingspagina | ✅ https://www.zorginzicht.nl/algemeen/open-data-medisch-specialistische-zorg-msz-ziekenhuizen-en-zelfstandige-behandelcentra |
| Overzicht alle sectoren | 🟡 https://www.zorginzicht.nl/openbare-data |
| Bestanden | ✅ "Openbaar databestand MSZ verslagjaar 2025": **Excel**, ~4,3 MB, plus "Naleveringen MSZ verslagjaar 2025" (~35 KB). De verslagjaren 2022–2025 zijn te downloaden. Sommige downloads zijn gecomprimeerd (zip). |
| Directe bestands-URL | ❓ Patroon dat elders op de site voorkomt: `https://www.zorginzicht.nl/binaries/content/assets/zorginzicht/openbare-data/<naam>.xlsx`. De exacte naam moet nog bevestigd worden. |
| Ritme | ✅ Jaarlijks. Ziekenhuizen leveren aan vóór 1 mei (verslagjaar 2025 → deadline 1 mei 2026), publicatie rond mei–juni. Volgende: verslagjaar 2026, deadline 1 mei 2027. |
| Dekt onze 3 ingrepen? | ✅ De transparantiekalender heeft aparte sets voor **Heupprothese**, **Knieprothese** en **Cataract**: https://www.zorginzicht.nl/transparantiekalender/medisch-specialistische-zorg |
| Definities indicatoren | ✅ bv. heup: https://zorginzicht.nl/binaries/content/assets/zorginzicht/kwaliteitsinstrumenten/indicatorengids-heupprothese---thp-verslagjaar-2025.pdf (gebaseerd op LROI: volume, revisies op korte termijn, PROMs; zonder heupfracturen) |
| Rapport datakwaliteit | ✅ https://zorginzicht.nl/binaries/content/assets/zorginzicht/openbare-data/rapportage-datakwaliteit-verslagjaar-2023-aanlevering-kwaliteitsgegevens-msz-mei-2024.pdf |
| Sleutel zorgaanbieder | ❓ Waarschijnlijk AGB-code + locatie; bevestigen aan de kolomkoppen in het Excel-bestand. |
| Licentie | ❓ Controleren op de landingspagina. Vragen of fouten: opendata@zinl.nl |

**Volgende stap:** het Excel-bestand van 2025 downloaden en de kolomnamen en de indicatoren voor THP/TKP/cataract op een rij zetten → `docs/zorginzicht_kolommen.md`.

## 2. Wachttijden: NZa

| | |
|---|---|
| Officiële dataset | ✅ "Dataset Wachttijden medisch-specialistische zorg": https://puc.overheid.nl/nza/doc/PUC_651798_22/ |
| Formaat | ✅ **CSV**, wordt **elke 2 weken** bijgewerkt, bevat de laatste peildatum en het jaar daarvoor (huidige versie: peildatum 15 sep 2026). |
| Directe bestands-URL | 🟡 NZa-documenten op puc.overheid.nl gebruiken `https://puc.overheid.nl/PUC/Handlers/DownloadDocument.ashx?identifier=PUC_651798_22&versienummer=<n>&type=csv`. Het versienummer verandert bij elke update, dus de scraper moet de laatste versie van de landingspagina halen. |
| Kolommen | 🟡 Bevat een nieuwe kolom `KVK_INSTELLING` (KvK-nummer van de instelling). De overige kolommen zijn ongewijzigd; de volledige lijst bevestigen aan de CSV. |
| API | 🟡 Er wordt een open API genoemd: `https://zorgbeeld.nza.nl/rest-doc/openapi`. Niet geverifieerd. |
| Wettelijke basis | ✅ Regeling Aanleveren wachttijden msz (NR/REG-2421); ziekenhuizen leveren maandelijks aan via het Zorgbeeldportaal. |
| Kanttekening | Niet door de NZa gecontroleerd op juistheid. Tonen als "opgegeven door het ziekenhuis". |

**Status (24-11-2026):** geblokkeerd. puc.overheid.nl gaf eerst HTTP 500 op robots.txt en weigert onze bot nu met HTTP 403 (ook op robots.txt). De API-paden op zorgbeeld.nza.nl geven ook 403. We omzeilen dat niet. Het verzoek om toegang staat klaar in `docs/nza_verzoek.md`.

**Conclusie:** de NZa-CSV rechtstreeks gebruiken. ZorgkaartNederland toont dezelfde NZa-data door en valt dus af. De CSV is open data en geeft alle locaties in één keer.

## 3. Contractstatus: ziekenhuizen × verzekeraars

### 3a. Contractpagina's van de ziekenhuizen zelf

Gevonden via zoekresultaten (allemaal op de eigen site van het ziekenhuis). Ze staan als `contracts_url` in
`data/manual/hospitals.csv`; `scrapers/contracts.py` haalt ze op (PDF én webpagina).

| Ziekenhuis | URL | Vorm | Status |
|---|---|---|---|
| Antoni van Leeuwenhoek | https://www.avl.nl/media/m0lbs1su/avl_contracten-zorgverzekeraars-2027-versie-3-november-2026.pdf | PDF-tabel per label | ✅ versie 3, nov 2026 |
| St. Antonius (Nieuwegein, Utrecht, Woerden) | https://www.antoniusziekenhuis.nl/kosten-en-zorgverzekering/contracten-met-zorgverzekeraars | webpagina | ✅ |
| Diakonessenhuis | https://www.diakonessenhuis.nl/nieuws/stand-zaken-contracten-zorgverzekeraars-2027 | nieuwsbericht | ✅ stand 13-11-2026 |
| Meander MC | https://www.meandermc.nl/praktische-informatie/kosten-en-vergoedingen/zorgverzekeraars-en-meander | webpagina | ✅ |
| Tergooi MC | https://www.tergooi.nl/afspraken-en-voorwaarden/ | webpagina | 🟡 geen datum zichtbaar |
| Gelderse Vallei | https://www.geldersevallei.nl/over-zgv/onderhandelingen-zorgverzekeraars | webpagina | ✅ |
| Rivierenland | https://www.ziekenhuisrivierenland.nl/naar-het-ziekenhuis/kosten-en-verzekering | webpagina | ✅ |
| Jeroen Bosch | https://www.jeroenboschziekenhuis.nl/naar-het-ziekenhuis/kosten-en-zorgverzekering/vergoeding-door-de-zorgverzekering | webpagina | 🟡 laatst gevonden bericht gaat over 2026 |
| UMC Utrecht | https://www.umcutrecht.nl/nl/budgetpolissen | webpagina | 🟡 geen 2027-overzicht; wel: geen contract voor budget-/selectieve polissen |
| Bergman Clinics (ZBC) | — | — | ❓ nog zoeken |

Let op: nieuwsberichten zoals dat van het Diakonessenhuis krijgen elk jaar een nieuwe URL. Elk najaar controleren.

### 3b. Eigen publicaties van verzekeraars (directe bron: de verzekeraar sluit het contract)

🟡 Verzekeraars moeten volgens NZa-regels zelf publiceren welke zorgaanbieders gecontracteerd zijn (nog bevestigen welke regeling dit precies voorschrijft). Hun zorgzoekers zijn daarom een directe bron, net als de overzichten van de ziekenhuizen. Waar beide bestaan, leggen we ze naast elkaar.

| Concern | URL | Status |
|---|---|---|
| CZ | ✅ `https://zorgvinder.cz.nl/resultaten/ziekenhuis/<plaats>?afstand=10&jaar=2027&...` | Leesbare parameters in de URL (plaats, afstand, **jaar**). Toont bv. voor UMC Utrecht 2027: "(Nog) geen contract: wel vergoed · Met omzetplafond". Goede eerste kandidaat. |
| VGZ | 🟡 https://www.vgz.nl/zorg-regelen/zorgzoeker | Toont omzetplafonds. JS-app, waarschijnlijk headless browser nodig. |
| Zilveren Kruis, Menzis, DSW, a.s.r., Zorg en Zekerheid | ❓ | nog opzoeken |

### 3c. Niet gebruiken als bron (platforms)
Zorgkiezer, Consumentenbond-contracteringsonderzoek e.d.: alleen om onze eigen uitkomst met de hand te controleren.

Achtergrond omzetplafonds: NZa-FAQ (mei 2026) https://puc.overheid.nl/PUC/Handlers/DownloadDocument.ashx?identifier=PUC_752361_22&versienummer=1&type=pdf&ValChk=wJGvp-IbIvXxY5bO9KawN_0ahok21uc1kmeb1fKvw5g1

## 4. Polissen en premies 2027

| Bron | URL | Status |
|---|---|---|
| Websites en polisvoorwaarden van de verzekeraars zelf | per label | **Hoofdbron.** Premie, polistype en vergoeding bij niet-gecontracteerde zorg staan in de polisvoorwaarden/het premieoverzicht van elk label. |
| Zorgverzekeringskaart (ZN) | 🟡 https://www.zorgverzekeringskaart.nl | Gevuld door de verzekeraars zelf via hun brancheorganisatie: semi-direct, goed als controlelijst van alle polissen. Geen export bekend. robots.txt nog checken. |
| NZa "polissen en premies" | ❓ | De NZa publiceert twee keer per jaar (informatiekaart, bv. over 2026 van 15 dec 2025: https://zoek.officielebekendmakingen.nl/dossier/blg-1228551.pdf). De editie over 2027 is waarschijnlijk nog niet uit (verwacht rond december). Checken of er een Excel-bijlage is. |
| Oude open data (2011–2016) | ✅ https://data.overheid.nl/dataset/5244-zorgverzekeringsmarkt--kenmerken-zorgverzekeringen-2011-2016 | Verouderd; alleen nuttig als model voor de kolommen. |

Feiten over 2027 uit nieuwsberichten (nog bevestigen bij de primaire bron): ONVZ valt per 1 jan 2027 onder VGZ; er zijn ongeveer 28 labels verdeeld over 9 concerns.

**Conclusie:** voor de MVP een handgemaakte `data/manual/polissen_2027.csv` bijhouden (ongeveer 60–70 polissen; premie + polistype + vergoeding niet-gecontracteerde zorg overnemen uit de polisvoorwaarden van de verzekeraar, met zorgverzekeringskaart.nl als controlelijst). Pas automatiseren als de NZa een bestand publiceert.

## 5. Referentietabel ziekenhuizen (AGB-codes)

| Bron | URL | Status |
|---|---|---|
| Vektis AGB-register | ✅ https://www.vektis.nl/agb-register | Dagelijks een volledige XML-dataset (betaald/onder voorwaarden), REST-"Raadpleegdienst" om op te zoeken. Bronvermelding "bron: Vektis" verplicht. |
| AGB opzoeken | 🟡 via de zoekfunctie van Vektis zelf (www.vektis.nl/agb-register) | Eén voor één opzoeken; prima voor ~71 ziekenhuizen + ~20 klinieken met de hand. Daarnaast staan AGB-codes vaak al in de Zorginzicht- en NZa-bestanden. |

**Conclusie:** `data/manual/hospitals.csv` met de hand opbouwen (AGB, naam, locaties, postcodes, aliassen), met de Zorginzicht- en NZa-bestanden als bron voor de namen en aliassen.

## 6. Patiëntervaring (voorheen: reviews)

ZorgkaartNederland is een platform en valt daarmee af als bron. **Geparkeerd** tot er een directe bron is:
- 🟡 Patiëntervaringsindicatoren (PREMs) die ziekenhuizen zelf aanleveren aan Zorginzicht, als die in het MSZ-bestand voor onze ingrepen zitten; de pipeline-inventaris (`docs/data_inventory/zorginzicht.md`) laat dit zien.
- De Patiëntenfederatie (eigenaar van de ZorgkaartNederland-data) om een officiële datalevering vragen. Dan is het een directe bron met afspraken.

## Andere bronnen voor later
- **LROI** (Landelijke Registratie Orthopedische Interventies): heup/knie-data per ziekenhuis; de basis van de Zorginzicht-indicatoren.
- **CBS / data.overheid.nl**: DBC-gegevens per diagnose (landelijk, niet per ziekenhuis).
- **Nulmeting transparantie Zorginstituut (apr 2026)**: https://www.zorginstituutnederland.nl/site/binaries/site-content/collections/documents/2026/04/02/rapport-inzicht-in-openbare-kwaliteitsinformatie-in-de-medisch-specialistische-zorg/rapport-inzicht-in-openbare-kwaliteitsinformatie-in-de-medisch-specialistische-zorg-nulmeting-transparantie.pdf
