# Beterverzekerd — overdracht voor Claude Code

Lees dit eerst. Het bevat alle context uit het verkennende gesprek (24 nov 2026) waarin dit project is bedacht.

## Over de eigenaar
- Nick, side project, los van zijn werk. Werkt in Utrecht.
- Geen echte programmeerachtergrond: leg stappen kort en concreet uit, kies simpele tooling, en laat hem niets handmatig in een terminal doen als het ook in code/CI kan.
- Communiceer in het Nederlands; code, comments en commit messages in het Engels.

## Probleem
Nederlandse zorgverzekeraars concurreren vooral op prijs, omdat consumenten de kwaliteit van de zorg die een verzekeraar inkoopt niet kunnen vergelijken. Bestaande tools tonen óf klantservice-reviews van verzekeraars (Zorgwijzer, Independer, ZorgkaartNederland), óf losse kwaliteitsinfo van ziekenhuizen (Zorginzicht, Ziekenhuischeck), óf contractstatus (Consumentenbond, alleen als afbeelding). Niemand koppelt die lagen.

Context: volgens de nulmeting van Zorginstituut + Patiëntenfederatie (april 2026) is voor slechts ~11,5% van de ziektelast in de medisch-specialistische zorg ten minste één uitkomstindicator openbaar (doel: 50%).

## Idee
Per polis × gecontracteerde ziekenhuizen × kwaliteit van die ziekenhuizen → "kwaliteitsscore per polis voor jouw zorgprofiel".
Gebruiker vult postcode + aandoening in en ziet per polis welke goede/snelle ziekenhuizen binnen bereik gecontracteerd zijn, met wachttijd, reviewcijfer en premie.

## MVP-scope
- Alleen ziekenhuizen en zelfstandige klinieken (medisch-specialistische zorg), ~71 ziekenhuisorganisaties.
- Een paar veelvoorkomende aandoeningen/ingrepen waar openbare data voor is. Startvoorstel: heupprothese, knieprothese, staaroperatie. Uitbreiden zodra de pijplijn werkt.
- De grote concerns met hun labels en polissen: Achmea (Zilveren Kruis e.a.), VGZ, CZ, Menzis, DSW, a.s.r., Zorg en Zekerheid (later: ONVZ — valt vanaf 2027 onder VGZ — Salland, Eucare).

## Architectuur (5 lagen)
1. **Bronnen** (elk eigen ververs-ritme)
   | Bron | Wat | Ritme | Hoe |
   |---|---|---|---|
   | Zorginzicht openbare data (Zorginstituut) | uitkomst- en volume-indicatoren per zorgaanbieder | ~jaarlijks | download open data (geen scraping nodig) |
   | Wachttijden (NZa) | wachttijd polikliniek/diagnostiek/behandeling per locatie | elke 2 weken | NZa open data (CSV op puc.overheid.nl); let op: niet gecontroleerd op juistheid |
   | Contracten | status per ziekenhuis × verzekeraar/label (gecontracteerd, met/zonder omzetplafond, in onderhandeling, geen contract) | 4× per overstapseizoen (nov–jan) | (a) contract-PDF's van ziekenhuizen zelf (bv. AVL, Jeroen Bosch publiceren tabellen per concern/label met peildatum); (b) eigen zorgzoekers van verzekeraars (JS-sites, headless browser nodig) |
   | Polissen & premies | polissen per label, premie, beperkende voorwaarden, vergoeding niet-gecontracteerd | jaarlijks (premies uiterlijk 12 nov) | polisvoorwaarden/premieoverzichten van de verzekeraars zelf + NZa-overzichten; zorgverzekeringskaart.nl (ZN) als controlelijst |
   | Patiëntervaring | gemiddeld cijfer + aantal waarderingen per ziekenhuis | — | GEPARKEERD: ZorgkaartNederland is een platform. Alleen via directe bron (PREMs in Zorginzicht, of datalevering Patiëntenfederatie); ALLEEN aggregaten |
2. **Ophalen**: per bron een los script in `scrapers/`. Eén kapotte bron mag de rest niet blokkeren. Ruwe output → `data/raw/<bron>/<peildatum>/`.
3. **Koppelen & opschonen** (`pipeline/`): sleutels zijn de AGB-code van het ziekenhuis (+ locatie) en een vaste mapping label → concern → polis. Ziekenhuisnamen verschillen per bron: bouw een `hospitals` referentietabel met aliassen.
4. **Database**: SQLite of DuckDB in het begin. Elk datapunt heeft `bron`, `peildatum`, `opgehaald_op`. Historie bewaren (contracten verschuiven door het seizoen).
5. **Score per polis + webapp** (`app/`): simpel beginnen (Streamlit of statische site). Toon bandbreedtes/"boven/onder landelijk gemiddelde" i.p.v. hard rangordes (ranglijsten van zorgaanbieders zijn methodologisch vaak misleidend: kleine aantallen, case-mix).

## Waar de scrapers draaien
De cloud-sandbox van Claude heeft beperkte internettoegang (allowlist), dus scrapers kunnen daar niet bij zorgsites. Opties:
- **GitHub Actions** (voorkeur): geplande workflows in `.github/workflows/` draaien de scrapers met gewoon internet en committen de data terug. Lost meteen het ververs-ritme op.
- Of lokaal op Nicks Windows-laptop (projecten staan in `OneDrive\Documenten pers\Projects`).

## Principes
- **Directe bronnen, geen platforms.** Data komt van de partij die haar maakt of beheert: Zorginstituut (Zorginzicht), NZa, Vektis (AGB), PDOK, de ziekenhuizen zelf en de verzekeraars zelf. Niet bouwen op vergelijkers of doorgeefluiken (Zorgkiezer, Zorgwijzer, Independer, Consumentenbond, ZorgkaartNederland, Apify-actors e.d.); die mogen hooguit als handmatige controle.
- Reviews: sla alleen gemiddeld cijfer + aantal op, geen reviewteksten of namen van individuele zorgverleners (AVG; databankenrecht van ZorgkaartNederland/Patiëntenfederatie). Overweeg de Patiëntenfederatie om data-toegang te vragen.
- Scrapen netjes: robots.txt respecteren, rate limiting, duidelijke User-Agent, cachen. Liefst open data en feitelijke contractstatus.
- Altijd bron + peildatum tonen; contractstatus is geen garantie op toegang (omzetplafonds, vergoeding tijdens onderhandeling).
- Disclaimer in de app: geen medisch of financieel advies.

## Eerste taken
1. `docs/bronnen.md` verifiëren: per bron de exacte URL's/downloadformaten checken (Zorginzicht open data voor heup/knie/staar).
2. Referentietabel ziekenhuizen + AGB-codes + aliassen.
3. Scraper contract-PDF's ziekenhuizen (start: 10 ziekenhuizen rond Utrecht) → genormaliseerde tabel.
4. Mapping label → concern → polissen 2027.
5. Zorginzicht-ingest voor de 3 ingrepen.
6. GitHub Action die 1 en 3 periodiek draait.
7. Eerste Streamlit-prototype: postcode + ingreep → tabel per polis.

## Open punten
- Naam gekozen: Beterverzekerd. Domein (.nl) en merknaam nog checken.
- Nick werkt bij NN Group (dat merk verkoopt zorgverzekeringen): nevenwerkzaamheden-regels checken vóór publicatie.
- Verdienmodel: onafhankelijk blijven (geen provisie) — abonnement, licentie aan patiëntenorganisaties/collectiviteiten, of non-profit.
