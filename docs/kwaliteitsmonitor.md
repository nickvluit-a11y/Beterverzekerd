# Kwaliteitsmonitor

Automatisch gemaakt door `pipeline/quality_monitor.py` uit de openbare kwaliteitsdata van Zorginzicht. Een ziekenhuis is alleen 'boven' of 'onder' gemiddeld als het verschil groter is dan de gebruikelijke spreiding tussen ziekenhuizen (95%-interval met correctie voor overdispersie). Geen ranglijst: kleine aantallen en verschillen in patiëntengroepen maken die misleidend.

**Let op patiëntenmix.** Alleen het revisiepercentage is gecorrigeerd voor patiëntkenmerken. Academische en topklinische centra behandelen vaker complexe patiënten en kunnen daardoor op ongecorrigeerde indicatoren (zoals PROM-verbetering en infecties) lager uitkomen zonder slechtere zorg. Zelfstandige klinieken behandelen juist vaker gezondere patiënten.

## Heupprothese

### Landelijk niveau per indicator

(percentages voor uitkomsten; gemiddelde verbetering in punten voor PROMs; mediaan van ziekenhuizen voor gecorrigeerde en gepubliceerde scores)

| indicator | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| Diepe wondinfectie binnen 90 dagen | 0.79 | 0.78 | 0.74 |  |
| Heroperatie (revisie) binnen 1 jaar | 0.60 | 0.64 | 0.65 | 0.74 |
| Verbetering volgens patiënt na 12 maanden: algemene gezondheid | 0.38 | 0.40 | 0.39 | 0.37 |
| Verbetering volgens patiënt na 12 maanden: eigen gezondheidscijfer | 13.46 | 14.18 | 13.59 | 13.18 |
| Verbetering volgens patiënt na 12 maanden: functie van de heup | 19.52 | 19.54 | 19.05 | 18.86 |
| Verbetering volgens patiënt na 12 maanden: pijn bij bewegen | 5.88 | 5.85 | 5.72 | 5.79 |
| Verbetering volgens patiënt na 12 maanden: pijn in rust | 4.39 | 4.34 | 4.30 | 4.33 |

### Aantal ziekenhuislocaties per oordeel

| verslagjaar | boven_gemiddeld | gemiddeld | gemengd | onder_gemiddeld | geen_data |
|---|---|---|---|---|---|
| 2022 | 22 | 48 | 3 | 12 | 0 |
| 2023 | 19 | 56 | 2 | 11 | 0 |
| 2024 | 19 | 58 | 2 | 9 | 0 |
| 2025 | 12 | 61 | 0 | 10 | 6 |

### Structureel boven gemiddeld (minstens 2 van 2023, 2024, 2025)

| ziekenhuis | jaren |
|---|---|
| Admiraal de Ruyter Ziekenhuis (Goes) | 2023, 2024, 2025 |
| Antonius Ziekenhuis Sneek (Sneek) | 2023, 2025 |
| Bergman Clinics / Bewegen / Rijswijk (Rijswijk) | 2023, 2024 |
| Bergman Clinics / Bewegen / Rotterdam (Rotterdam) | 2024, 2025 |
| CortoClinics B.V. (Nederweert) | 2024, 2025 |
| Kliniek ViaSana (Mill) | 2024, 2025 |
| Noordwest Ziekenhuisgroep, concern (Alkmaar) | 2023, 2024, 2025 |
| Rivas Zorggroep, Beatrixziekenhuis (Gorinchem) | 2023, 2024, 2025 |
| Rode Kruis Ziekenhuis BV (Beverwijk) | 2023, 2024 |
| Sint Jans Gasthuis (Weert) | 2023, 2024 |
| Stichting Park Medisch Centrum (Rotterdam) | 2023, 2024, 2025 |

### Structureel onder gemiddeld (minstens 2 van 2023, 2024, 2025)

| ziekenhuis | jaren |
|---|---|
| Albert Schweitzer Ziekenhuis (Dordrecht) | 2024, 2025 |
| Amphia ziekenhuis (Breda) | 2023, 2025 |
| Amsterdam UMC - concern (Amsterdam) | 2023, 2024 |
| Reinier Haga Groep Orthopedisch Centrum B.V. (Zoetermeer) | 2023, 2024 |
| St. Anna Ziekenhuis (Geldrop) | 2023, 2024 |
| Stichting Martini Ziekenhuis (Groningen) | 2023, 2025 |
| Ziekenhuis Nij Smellinghe (Drachten) | 2024, 2025 |

### Verbeterd van 2024 naar 2025

| ziekenhuis | 2024 | 2025 |
|---|---|---|
| Amsterdam UMC - concern (Amsterdam) | onder_gemiddeld | gemiddeld |
| Antonius Ziekenhuis Sneek (Sneek) | gemiddeld | boven_gemiddeld |
| Bergman Clinics / Bewegen / Arnhem (ARNHEM) | gemiddeld | boven_gemiddeld |
| Dijklander Ziekenhuis (Hoorn) | onder_gemiddeld | gemiddeld |
| Isala concern (Zwolle) | gemiddeld | boven_gemiddeld |
| Meander Medisch Centrum (Amersfoort) | onder_gemiddeld | gemiddeld |
| Medisch Spectrum Twente (Enschede) | onder_gemiddeld | gemiddeld |
| Ommelander Ziekenhuis Groningen (Scheemda) | gemiddeld | boven_gemiddeld |
| Reinier Haga Groep Orthopedisch Centrum B.V. (Zoetermeer) | onder_gemiddeld | gemiddeld |
| St. Anna Ziekenhuis (Geldrop) | onder_gemiddeld | gemiddeld |
| Stichting Gelre Ziekenhuizen (Apeldoorn) | gemiddeld | boven_gemiddeld |
| Zuyderland Medisch Centrum (Heerlen) | onder_gemiddeld | gemiddeld |

### Verslechterd van 2024 naar 2025

| ziekenhuis | 2024 | 2025 |
|---|---|---|
| Amphia ziekenhuis (Breda) | gemiddeld | onder_gemiddeld |
| Bergman Clinics / Bewegen / Breda (BREDA) | gemiddeld | onder_gemiddeld |
| Bergman Clinics / Bewegen / Naarden (Naarden) | boven_gemiddeld | onder_gemiddeld |
| Bergman Clinics / Bewegen / Rijswijk (Rijswijk) | boven_gemiddeld | gemiddeld |
| Canisius Wilhelmina Ziekenhuis (Nijmegen) | boven_gemiddeld | gemiddeld |
| Franciscus Concern (Rotterdam) | boven_gemiddeld | gemiddeld |
| Frisius MC, locatie Heerenveen (Heerenveen) | boven_gemiddeld | gemiddeld |
| Ijsselland ziekenhuis (Capelle a/d IJssel) | boven_gemiddeld | gemiddeld |
| Rode Kruis Ziekenhuis BV (Beverwijk) | boven_gemiddeld | gemiddeld |
| Sint Jans Gasthuis (Weert) | boven_gemiddeld | onder_gemiddeld |
| Stichting Martini Ziekenhuis (Groningen) | gemiddeld | onder_gemiddeld |
| Streekziekenhuis Koningin Beatrix Winterswijk (Winterswijk) | boven_gemiddeld | gemiddeld |
| Wilhelmina Ziekenhuis Assen (Assen) | boven_gemiddeld | onder_gemiddeld |
| Xpert Clinics Rotterdam (Rotterdam) | boven_gemiddeld | gemiddeld |
| Ziekenhuis Amstelland (Amstelveen) | gemiddeld | onder_gemiddeld |
| ZorgSaam Ziekenhuis (Terneuzen) | gemiddeld | onder_gemiddeld |

## Knieprothese

### Landelijk niveau per indicator

(percentages voor uitkomsten; gemiddelde verbetering in punten voor PROMs; mediaan van ziekenhuizen voor gecorrigeerde en gepubliceerde scores)

| indicator | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| Diepe wondinfectie binnen 90 dagen | 0.64 | 0.58 | 0.56 |  |
| Heroperatie (revisie) binnen drie jaar | 0.74 | 0.95 | 0.78 | 0.77 |
| Verbetering volgens patiënt na 12 maanden: algemene gezondheid | 0.31 | 0.33 | 0.32 | 0.30 |
| Verbetering volgens patiënt na 12 maanden: eigen gezondheidscijfer | 8.73 | 8.78 | 9.38 | 9.17 |
| Verbetering volgens patiënt na 12 maanden: functie van de knie | 15.67 | 15.75 | 15.37 | 15.31 |
| Verbetering volgens patiënt na 12 maanden: pijn bij bewegen | 4.95 | 5.01 | 4.95 | 4.95 |
| Verbetering volgens patiënt na 12 maanden: pijn in rust | 3.68 | 3.59 | 3.63 | 3.52 |

### Aantal ziekenhuislocaties per oordeel

| verslagjaar | boven_gemiddeld | gemiddeld | gemengd | onder_gemiddeld | geen_data |
|---|---|---|---|---|---|
| 2022 | 26 | 47 | 2 | 10 | 1 |
| 2023 | 31 | 50 | 0 | 6 | 0 |
| 2024 | 29 | 48 | 2 | 8 | 0 |
| 2025 | 10 | 57 | 1 | 10 | 11 |

### Structureel boven gemiddeld (minstens 2 van 2023, 2024, 2025)

| ziekenhuis | jaren |
|---|---|
| Admiraal de Ruyter Ziekenhuis (Goes) | 2023, 2024, 2025 |
| Antonius Ziekenhuis Sneek (Sneek) | 2023, 2024 |
| Bovenij Ziekenhuis (Amsterdam) | 2023, 2024 |
| Canisius Wilhelmina Ziekenhuis (Nijmegen) | 2023, 2024 |
| CortoClinics B.V. (Nederweert) | 2024, 2025 |
| Frisius MC, locatie Leeuwarden (Leeuwarden) | 2023, 2024, 2025 |
| Groene Hart Ziekenhuis (Gouda) | 2023, 2024 |
| Ijsselland ziekenhuis (Capelle a/d IJssel) | 2023, 2024 |
| Meander Medisch Centrum (Amersfoort) | 2023, 2024 |
| Rivas Zorggroep, Beatrixziekenhuis (Gorinchem) | 2023, 2024, 2025 |
| Saxenburgh Medisch Centrum (Hardenberg) | 2023, 2024, 2025 |
| Stichting Laurentius Ziekenhuis Roermond (Roermond) | 2023, 2024 |
| Stichting Park Medisch Centrum (Rotterdam) | 2023, 2024 |
| Zaans Medisch Centrum (Zaandam) | 2023, 2024 |
| Ziekenhuis Amstelland (Amstelveen) | 2023, 2024 |
| Ziekenhuis Nij Smellinghe (Drachten) | 2023, 2024 |

### Structureel onder gemiddeld (minstens 2 van 2023, 2024, 2025)

| ziekenhuis | jaren |
|---|---|
| Frisius MC, locatie Heerenveen (Heerenveen) | 2024, 2025 |
| Het Flevoziekenhuis (Almere) | 2023, 2025 |
| OLVG Concern (Amsterdam) | 2023, 2024 |
| Stichting Gelre Ziekenhuizen (Apeldoorn) | 2023, 2024 |
| VieCuri Medisch centrum voor NoordLimburg (Venlo) | 2023, 2025 |

### Verbeterd van 2024 naar 2025

| ziekenhuis | 2024 | 2025 |
|---|---|---|
| Dijklander Ziekenhuis (Hoorn) | gemiddeld | boven_gemiddeld |
| Maxima Medisch Centrum (Veldhoven) | onder_gemiddeld | gemiddeld |
| Medisch Spectrum Twente (Enschede) | onder_gemiddeld | gemiddeld |
| OLVG Concern (Amsterdam) | onder_gemiddeld | gemiddeld |
| Ommelander Ziekenhuis Groningen (Scheemda) | gemiddeld | boven_gemiddeld |
| Reinier Haga Groep Orthopedisch Centrum B.V. (Zoetermeer) | gemiddeld | boven_gemiddeld |
| Stichting Gelre Ziekenhuizen (Apeldoorn) | onder_gemiddeld | gemiddeld |
| Stichting het van Weel-Bethesda Ziekenhuis, Dirksland (Dirksland) | onder_gemiddeld | gemiddeld |
| UMC Groningen (Groningen) | onder_gemiddeld | gemiddeld |
| Ziekenhuis Rijnstate (Arnhem) | onder_gemiddeld | gemiddeld |
| Ziekenhuis St Jansdal (Harderwijk) | gemiddeld | boven_gemiddeld |
| ZorgSaam Ziekenhuis (Terneuzen) | gemiddeld | boven_gemiddeld |

### Verslechterd van 2024 naar 2025

| ziekenhuis | 2024 | 2025 |
|---|---|---|
| Albert Schweitzer Ziekenhuis (Dordrecht) | gemiddeld | onder_gemiddeld |
| Antonius Ziekenhuis Sneek (Sneek) | boven_gemiddeld | gemengd |
| Bergman Clinics / Bewegen / Rijswijk (Rijswijk) | gemiddeld | onder_gemiddeld |
| Bovenij Ziekenhuis (Amsterdam) | boven_gemiddeld | gemiddeld |
| Canisius Wilhelmina Ziekenhuis (Nijmegen) | boven_gemiddeld | gemiddeld |
| Elkerliek ziekenhuis (Helmond) | boven_gemiddeld | gemiddeld |
| Groene Hart Ziekenhuis (Gouda) | boven_gemiddeld | gemiddeld |
| Het Flevoziekenhuis (Almere) | boven_gemiddeld | onder_gemiddeld |
| Ijsselland ziekenhuis (Capelle a/d IJssel) | boven_gemiddeld | gemiddeld |
| Interconfessionele Stichting Gezondheidszorg Rivierenland (Tiel) | boven_gemiddeld | gemiddeld |
| Maasstadziekenhuis (Rotterdam) | boven_gemiddeld | gemiddeld |
| Meander Medisch Centrum (Amersfoort) | boven_gemiddeld | gemiddeld |
| Sint Antonius Ziekenhuis, concern (Nieuwegein) | gemiddeld | onder_gemiddeld |
| Sint Jans Gasthuis (Weert) | gemengd | onder_gemiddeld |
| Sint Maartenskliniek, concern (Ubbergen) | gemiddeld | onder_gemiddeld |
| Spijkenisse Medisch Centrum (Spijkenisse) | boven_gemiddeld | gemiddeld |
| Stichting Acibadem International Medical Center (Amsterdam) | boven_gemiddeld | onder_gemiddeld |
| Stichting Catharina Ziekenhuis (Eindhoven) | boven_gemiddeld | gemiddeld |
| Stichting Laurentius Ziekenhuis Roermond (Roermond) | boven_gemiddeld | gemiddeld |
| Stichting Martini Ziekenhuis (Groningen) | boven_gemiddeld | gemiddeld |
| Stichting Park Medisch Centrum (Rotterdam) | boven_gemiddeld | gemiddeld |
| Tergooi MC (Hilversum) | boven_gemiddeld | gemiddeld |
| VieCuri Medisch centrum voor NoordLimburg (Venlo) | boven_gemiddeld | onder_gemiddeld |
| Wilhelmina Ziekenhuis Assen (Assen) | boven_gemiddeld | gemiddeld |
| Xpert Clinics Utrecht Janssoniuslaan (Utrecht) | boven_gemiddeld | gemiddeld |
| Ziekenhuis Amstelland (Amstelveen) | boven_gemiddeld | gemiddeld |
| Ziekenhuis Gelderse Vallei (Ede Gld.) | gemiddeld | onder_gemiddeld |
| Ziekenhuis Nij Smellinghe (Drachten) | boven_gemiddeld | gemiddeld |

## Staaroperatie (cataract)

### Landelijk niveau per indicator

(percentages voor uitkomsten; gemiddelde verbetering in punten voor PROMs; mediaan van ziekenhuizen voor gecorrigeerde en gepubliceerde scores)

| indicator | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| Minstens 1 regel beter zien | 95.79 | 95.22 | 94.47 | 94.49 |
| Refractie binnen 0.5 dioptrie van doel |  |  |  | 77.88 |
| Refractie binnen 1 dioptrie van doel | 94.94 | 94.66 | 94.75 |  |

### Aantal ziekenhuislocaties per oordeel

| verslagjaar | boven_gemiddeld | gemiddeld | gemengd | onder_gemiddeld | geen_data |
|---|---|---|---|---|---|
| 2022 | 25 | 63 | 0 | 9 | 3 |
| 2023 | 27 | 62 | 0 | 9 | 4 |
| 2024 | 26 | 50 | 0 | 11 | 1 |
| 2025 | 22 | 66 | 3 | 11 | 8 |

### Structureel boven gemiddeld (minstens 2 van 2023, 2024, 2025)

| ziekenhuis | jaren |
|---|---|
| Admiraal de Ruyter Ziekenhuis (Goes) | 2023, 2024, 2025 |
| Bergman Clinics / Ogen / Amersfoort (Amersfoort) | 2023, 2024, 2025 |
| Bergman Clinics / Ogen / Doetinchem (Doetinchem) | 2023, 2024, 2025 |
| Bergman Clinics / Ogen / Hoogeveen (Hoogeveen) | 2023, 2024, 2025 |
| Bergman Clinics / Ogen / Lelystad (Lelystad) | 2023, 2024, 2025 |
| Diakonessenhuis Utrecht, Zeist, Doorn (Utrecht) | 2023, 2024 |
| Ikazia Ziekenhuis Rotterdam (Rotterdam) | 2024, 2025 |
| Iris Eye Clinics (Boxtel) | 2023, 2024, 2025 |
| OLVG Concern (Amsterdam) | 2023, 2024, 2025 |
| Ommelander Ziekenhuis Groningen (Scheemda) | 2023, 2024 |
| Oogkliniek Maastricht (Maastricht) | 2023, 2025 |
| Rivas Zorggroep, Beatrixziekenhuis (Gorinchem) | 2023, 2024, 2025 |
| Saxenburgh Medisch Centrum (Hardenberg) | 2023, 2024 |
| Sint Antonius Ziekenhuis, concern (Nieuwegein) | 2024, 2025 |
| Stichting Eye P. (Driebergen) | 2023, 2024, 2025 |
| Stichting HagaZiekenhuis (Den Haag) | 2024, 2025 |
| Stichting Laurentius Ziekenhuis Roermond (Roermond) | 2023, 2024 |
| Stichting Martini Ziekenhuis (Groningen) | 2023, 2024, 2025 |
| VieCuri Medisch centrum voor NoordLimburg (Venlo) | 2023, 2025 |
| Wilhelmina Ziekenhuis Assen (Assen) | 2023, 2024, 2025 |
| Ziekenhuis Nij Smellinghe (Drachten) | 2023, 2024 |
| Ziekenhuis St Jansdal (Harderwijk) | 2023, 2024, 2025 |

### Structureel onder gemiddeld (minstens 2 van 2023, 2024, 2025)

| ziekenhuis | jaren |
|---|---|
| Concernniveau: Stolmed Klinieken (Bergen op Zoom) | 2023, 2024 |
| Maasziekenhuis Pantein (Beugen) | 2024, 2025 |
| Radboud UMC (Nijmegen) | 2023, 2024, 2025 |
| Spijkenisse Medisch Centrum (Spijkenisse) | 2023, 2024 |
| Stichting Oog Medisch Centrum Zaandam (Zaandam) | 2023, 2025 |
| UMC Utrecht (Utrecht) | 2024, 2025 |

### Verbeterd van 2024 naar 2025

| ziekenhuis | 2024 | 2025 |
|---|---|---|
| Bergman Clinics / Ogen / Hilversum (Hilversum) | gemiddeld | boven_gemiddeld |
| Concernniveau: Stolmed Klinieken (Bergen op Zoom) | onder_gemiddeld | gemiddeld |
| Dr. Binkhorst Eye Center (Terneuzen) | onder_gemiddeld | boven_gemiddeld |
| Franciscus Concern (Rotterdam) | onder_gemiddeld | gemiddeld |
| Oog en Welzijn B.V. (DOKKUM) | onder_gemiddeld | gemiddeld |
| Oogcentrum Noordholland B.V. (Heerhugowaard) | onder_gemiddeld | gemiddeld |
| Sint Jans Gasthuis (Weert) | onder_gemiddeld | gemiddeld |
| Spaarne Gasthuis, concern (Haarlem) | gemiddeld | boven_gemiddeld |
| Spijkenisse Medisch Centrum (Spijkenisse) | onder_gemiddeld | gemiddeld |
| Treant Zorggroep (Hoogeveen) | gemiddeld | boven_gemiddeld |
| VieCuri Medisch centrum voor NoordLimburg (Venlo) | gemiddeld | boven_gemiddeld |

### Verslechterd van 2024 naar 2025

| ziekenhuis | 2024 | 2025 |
|---|---|---|
| Amphia ziekenhuis (Breda) | gemiddeld | onder_gemiddeld |
| Bergman Clinics / Ogen / Den Bosch (Den Bosch) | gemiddeld | onder_gemiddeld |
| Diakonessenhuis Utrecht, Zeist, Doorn (Utrecht) | boven_gemiddeld | gemengd |
| Dijklander Ziekenhuis (Hoorn) | gemiddeld | onder_gemiddeld |
| Frisius MC, locatie Heerenveen (Heerenveen) | boven_gemiddeld | gemiddeld |
| Frisius MC, locatie Leeuwarden (Leeuwarden) | boven_gemiddeld | gemiddeld |
| Meander Medisch Centrum (Amersfoort) | boven_gemiddeld | gemiddeld |
| Ommelander Ziekenhuis Groningen (Scheemda) | boven_gemiddeld | gemiddeld |
| Oogkliniek Den Haag B.V. (Den Haag) | gemiddeld | onder_gemiddeld |
| Saxenburgh Medisch Centrum (Hardenberg) | boven_gemiddeld | gemengd |
| St. Anna Ziekenhuis (Geldrop) | gemiddeld | onder_gemiddeld |
| Stichting Catharina Ziekenhuis (Eindhoven) | gemiddeld | onder_gemiddeld |
| Stichting Laurentius Ziekenhuis Roermond (Roermond) | boven_gemiddeld | gemiddeld |
| Stichting Oogartsenpraktijk Delfland (DELFT) | gemiddeld | onder_gemiddeld |
| Stichting Oogcentrum Eibergen (EIBERGEN) | boven_gemiddeld | gemiddeld |
| Stichting VISUS (ROTTERDAM) | boven_gemiddeld | gemiddeld |
| Xpert Clinics oogzorg Zeist (Zeist) | boven_gemiddeld | gemiddeld |
| Ziekenhuis Nij Smellinghe (Drachten) | boven_gemiddeld | gemiddeld |
