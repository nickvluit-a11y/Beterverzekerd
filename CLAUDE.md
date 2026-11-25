# Beterverzekerd — overdracht voor Claude Code

Lees dit eerst. Het bevat alle context uit het verkennende gesprek (24 nov 2026) waarin dit project is bedacht.

## Over de eigenaar
- Nick, side project, los van zijn werk. Werkt in Utrecht.
- Geen echte programmeerachtergrond: leg stappen kort en concreet uit, kies simpele tooling, en laat hem niets handmatig in een terminal doen als het ook in code/CI kan.
- Communiceer in het Nederlands; code, comments en commit messages in het Engels.

## Probleem
Nederlandse zorgverzekeraars concurreren vooral op prijs, omdat consumenten de kwaliteit van de zorg die een verzekeraar inkoopt niet kunnen vergelijken. Bestaande tools tonen óf klantservice-reviews van verzekeraars (Zorgwijzer, Independer, ZorgkaartNederland), óf losse kwaliteitsinfo van ziekenhuizen (Zorginzicht, Ziekenhuischeck), óf contractstatus (Consumentenbond, alleen als afbeelding). Niemand koppelt die lagen.

Context: volgens de nulmeting van Zorginstituut + Patiëntenfederatie (april 2026) is voor slechts ~11,5% van de ziektelast in de medisch-specialistische zorg ten minste één uitkomstindicator openbaar (doel: 50%).

## USP (toets elke keuze hieraan)
**Kwaliteit zichtbaar maken.** Consumenten moeten polissen kunnen vergelijken op de kwaliteit van de zorg die de verzekeraar voor hen inkoopt, niet alleen op premie. Pas dan gaan verzekeraars concurreren op prijs én kwaliteit. Kwaliteit staat daarom vooraan in de app (vóór premie en contractaantallen), en elke bron, berekening of schermwijziging moet dat doel dienen.

## Werkwijze in deze fase
**Klein en heel goed.** Liever één ding uitstekend dan veel dingen net niet. De kernvraag van de app: *"Welke ziekenhuizen bij mij in de buurt zijn aantoonbaar beter voor mijn ingreep, en kan ik daar terecht met mijn verzekering?"* Alles wat daar niet direct aan bijdraagt, wacht.
**Overzichtelijk en mooi.** Volg het format van de zorgzoekers van grote verzekeraars en vergelijkers: één zoekbalk, kaart + lijst met kaartjes (naam, plaats, afstand, één duidelijk label, 2–3 kernpunten in gewone taal), details pas na een klik. Geen brede tabellen op het eerste scherm.

## Scope-besluit (eigenaar, 25-11-2026)
**Directe bronnen gaan vóór volledigheid.** Liever een selectie die we rechtstreeks bij de bron kunnen ophalen dan alles via platforms of diep weggestopte pagina's. Daarom dekt de app voorlopig alleen de **vier grootste verzekeraarsconcerns**: Zilveren Kruis (Achmea, 28,2%), VGZ (23,6%), CZ (22,2%) en Menzis (10,7%): samen ±85% van de verzekerden. Bevestigd door de eigenaar op 25-11-2026: met deze vier zijn we redelijk volledig; daar ligt de focus, niet meer. Vastgelegd in `data/manual/scope.csv`. Premies, polissen en contractstatus komen van hun eigen sites en zorgzoekers; een test bewaakt dat elke getoonde polis een bron op het eigen domein heeft. Andere concerns (DSW, a.s.r., Zorg en Zekerheid, ONVZ, Salland, Eucare) vallen buiten scope. Alle merken van de vier (bv. FBTO, Univé, OHRA, VinkVink) zijn kiesbaar; zonder eigen data volgen ze de contracten van het hoofdmerk van hun concern, met die vermelding. Premies tonen we alleen voor de hoofdmerken (eigen site). Geen ZorgkaartNederland (besluit eigenaar 25-11-2026: platform, geen kwaliteitsmaat). De drempels voor 'beter' (80%) en 'slechter' (95%) blijven asymmetrisch (besluit eigenaar).

## Idee
Per polis × gecontracteerde ziekenhuizen × kwaliteit van die ziekenhuizen → "kwaliteitsscore per polis voor jouw zorgprofiel".
Gebruiker vult postcode + aandoening in en ziet per polis welke goede/snelle ziekenhuizen binnen bereik gecontracteerd zijn, met wachttijd, reviewcijfer en premie.

## MVP-scope
- Alleen ziekenhuizen en zelfstandige klinieken (medisch-specialistische zorg), ~71 ziekenhuisorganisaties.
- Een paar veelvoorkomende aandoeningen/ingrepen waar openbare data voor is. Startvoorstel: heupprothese, knieprothese, staaroperatie. Uitbreiden zodra de pijplijn werkt.
- Verzekeraars: zie Scope-besluit (de vier grootste, hoofdmerk). Later eventueel DSW, a.s.r., Zorg en Zekerheid e.a., alleen met directe bronnen.

## Architectuur (5 lagen)
1. **Bronnen** (elk eigen ververs-ritme)
   | Bron | Wat | Ritme | Hoe |
   |---|---|---|---|
   | Zorginzicht openbare data (Zorginstituut) | uitkomst- en volume-indicatoren per zorgaanbieder | ~jaarlijks | download open data (geen scraping nodig) |
   | Wachttijden (NZa) | wachttijd polikliniek/diagnostiek/behandeling per locatie | elke 2 weken | NZa open data (CSV op puc.overheid.nl); let op: niet gecontroleerd op juistheid |
   | Contracten | status per ziekenhuis × verzekeraar/label (gecontracteerd, met/zonder omzetplafond, in onderhandeling, geen contract) | 4× per overstapseizoen (nov–jan) | (a) contract-PDF's van ziekenhuizen zelf (bv. AVL, Jeroen Bosch publiceren tabellen per concern/label met peildatum); (b) eigen zorgzoekers van verzekeraars (JS-sites, headless browser nodig) |
   | Polissen & premies | polissen per label, premie, beperkende voorwaarden, vergoeding niet-gecontracteerd | jaarlijks (premies uiterlijk 12 nov) | polisvoorwaarden/premieoverzichten van de verzekeraars zelf + NZa-overzichten; zorgverzekeringskaart.nl (ZN) als controlelijst |
   | Patiëntervaring | — | — | Niet in de app: ZorgkaartNederland is een platform (besluit eigenaar 25-11-2026). Patiënt-gerapporteerde uitkomsten (PROMs) komen wél mee via Zorginzicht. |
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
