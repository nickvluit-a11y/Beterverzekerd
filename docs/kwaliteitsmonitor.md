# Kwaliteitsmonitor

Automatisch gemaakt door `pipeline/quality_monitor.py` uit de openbare kwaliteitsdata van Zorginzicht. Een ziekenhuis is alleen 'boven' of 'onder' gemiddeld als het verschil groter is dan de gebruikelijke spreiding tussen ziekenhuizen (95%-interval met correctie voor overdispersie). Geen ranglijst: kleine aantallen en verschillen in patiëntengroepen maken die misleidend.

**Let op patiëntenmix.** Alleen het revisiepercentage is gecorrigeerd voor patiëntkenmerken. Academische en topklinische centra behandelen vaker complexe patiënten en kunnen daardoor op ongecorrigeerde indicatoren (zoals PROM-verbetering en infecties) lager uitkomen zonder slechtere zorg. Zelfstandige klinieken behandelen juist vaker gezondere patiënten.

## Heupprothese

### Landelijk niveau per indicator

(percentages voor uitkomsten; gemiddelde verbetering in punten voor PROMs; mediaan van ziekenhuizen voor gecorrigeerde en gepubliceerde scores)

| indicator | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| Diepe wondinfectie binnen 90 dagen | 0.79 | 0.78 | 0.74 | 1.00 |
| Revisie binnen 1 jaar (gecorrigeerd) | 0.96 | 0.89 | 1.06 | 1.00 |
| Verbetering volgens patiënt na 12 mnd: EQ-5D index | 0.38 | 0.40 | 0.38 | 0.36 |
| Verbetering volgens patiënt na 12 mnd: EQ-5D thermometer | 13.04 | 14.04 | 13.55 | 11.90 |
| Verbetering volgens patiënt na 12 mnd: NRS-pijn activiteit | 5.86 | 5.74 | 5.67 | 5.65 |
| Verbetering volgens patiënt na 12 mnd: NRS-pijn rust | 4.32 | 4.31 | 4.26 | 4.16 |
| Verbetering volgens patiënt na 12 mnd: OHS | 19.15 | 19.19 | 18.87 | 18.42 |

### Aantal ziekenhuislocaties per oordeel

| verslagjaar | boven_gemiddeld | gemiddeld | gemengd | onder_gemiddeld | geen_data |
|---|---|---|---|---|---|
| 2022 | 13 | 46 | 4 | 22 | 0 |
| 2023 | 12 | 58 | 2 | 16 | 0 |
| 2024 | 12 | 60 | 1 | 15 | 0 |
| 2025 | 16 | 60 | 0 | 10 | 3 |

### Structureel boven gemiddeld (minstens 2 van 2023, 2024, 2025)

| ziekenhuis | jaren |
|---|---|
| Admiraal de Ruyter Ziekenhuis (Goes) | 2023, 2024, 2025 |
| Antonius Ziekenhuis Sneek (Sneek) | 2023, 2024, 2025 |
| Bergman Clinics / Bewegen / Naarden (Naarden) | 2023, 2024 |
| Bergman Clinics / Bewegen / Rijswijk (Rijswijk) | 2023, 2024 |
| Kliniek ViaSana (Mill) | 2024, 2025 |
| Noordwest Ziekenhuisgroep, concern (Alkmaar) | 2023, 2024, 2025 |
| Ommelander Ziekenhuis Groningen (Scheemda) | 2023, 2025 |
| Rivas Zorggroep, Beatrixziekenhuis (Gorinchem) | 2024, 2025 |
| Stichting Park Medisch Centrum (Rotterdam) | 2023, 2024, 2025 |
| Ziekenhuis Gelderse Vallei (Ede Gld.) | 2023, 2024 |

### Structureel onder gemiddeld (minstens 2 van 2023, 2024, 2025)

| ziekenhuis | jaren |
|---|---|
| Albert Schweitzer Ziekenhuis (Dordrecht) | 2024, 2025 |
| Amsterdam UMC - concern (Amsterdam) | 2023, 2024 |
| Erasmus MC (Rotterdam) | 2023, 2024 |
| Groene Hart Ziekenhuis (Gouda) | 2024, 2025 |
| Medisch Spectrum Twente (Enschede) | 2023, 2024 |
| Sint Jans Gasthuis (Weert) | 2024, 2025 |
| Stichting Acibadem International Medical Center (Amsterdam) | 2023, 2024 |
| Stichting Gelre Ziekenhuizen (Apeldoorn) | 2023, 2024 |
| Stichting Martini Ziekenhuis (Groningen) | 2023, 2025 |
| ZorgSaam Ziekenhuis (Terneuzen) | 2024, 2025 |

### Verbeterd van 2024 naar 2025

| ziekenhuis | 2024 | 2025 |
|---|---|---|
| Amsterdam UMC - concern (Amsterdam) | onder_gemiddeld | gemiddeld |
| Bergman Clinics / Bewegen / Arnhem (ARNHEM) | gemiddeld | boven_gemiddeld |
| Bergman Clinics / Bewegen / Rotterdam (Rotterdam) | gemiddeld | boven_gemiddeld |
| Bovenij Ziekenhuis (Amsterdam) | gemiddeld | boven_gemiddeld |
| CortoClinics B.V. (Nederweert) | gemiddeld | boven_gemiddeld |
| Erasmus MC (Rotterdam) | onder_gemiddeld | gemiddeld |
| Frisius MC, locatie Leeuwarden (Leeuwarden) | gemiddeld | boven_gemiddeld |
| Ijsselland ziekenhuis (Capelle a/d IJssel) | onder_gemiddeld | gemiddeld |
| Isala concern (Zwolle) | gemiddeld | boven_gemiddeld |
| Meander Medisch Centrum (Amersfoort) | onder_gemiddeld | gemiddeld |
| Medisch Spectrum Twente (Enschede) | onder_gemiddeld | gemiddeld |
| OLVG Concern (Amsterdam) | onder_gemiddeld | gemiddeld |
| Ommelander Ziekenhuis Groningen (Scheemda) | gemiddeld | boven_gemiddeld |
| Radboud UMC (Nijmegen) | onder_gemiddeld | gemiddeld |
| Saxenburgh Medisch Centrum (Hardenberg) | gemiddeld | boven_gemiddeld |
| Stichting Acibadem International Medical Center (Amsterdam) | onder_gemiddeld | gemiddeld |
| Stichting Gelre Ziekenhuizen (Apeldoorn) | onder_gemiddeld | gemiddeld |
| UMC Groningen (Groningen) | gemiddeld | boven_gemiddeld |
| Ziekenhuis Amstelland (Amstelveen) | onder_gemiddeld | gemiddeld |
| Ziekenhuis Rijnstate (Arnhem) | gemiddeld | boven_gemiddeld |
| Zuyderland Medisch Centrum (Heerlen) | onder_gemiddeld | gemiddeld |

### Verslechterd van 2024 naar 2025

| ziekenhuis | 2024 | 2025 |
|---|---|---|
| Amphia ziekenhuis (Breda) | gemiddeld | onder_gemiddeld |
| Bergman Clinics / Bewegen / Breda (BREDA) | gemiddeld | onder_gemiddeld |
| Bergman Clinics / Bewegen / Naarden (Naarden) | boven_gemiddeld | gemiddeld |
| Bergman Clinics / Bewegen / Rijswijk (Rijswijk) | boven_gemiddeld | gemiddeld |
| Canisius Wilhelmina Ziekenhuis (Nijmegen) | boven_gemiddeld | gemiddeld |
| Haaglanden Medisch Centrum (Den Haag) | boven_gemiddeld | gemiddeld |
| Sint Maartenskliniek, concern (Ubbergen) | gemiddeld | onder_gemiddeld |
| Stichting Martini Ziekenhuis (Groningen) | gemiddeld | onder_gemiddeld |
| Wilhelmina Ziekenhuis Assen (Assen) | gemiddeld | onder_gemiddeld |
| Xpert Clinics Eindhoven Holtoplaan (Eindhoven) | boven_gemiddeld | gemiddeld |
| Ziekenhuis Gelderse Vallei (Ede Gld.) | boven_gemiddeld | gemiddeld |
| Ziekenhuis Nij Smellinghe (Drachten) | gemiddeld | onder_gemiddeld |

## Knieprothese

### Landelijk niveau per indicator

(percentages voor uitkomsten; gemiddelde verbetering in punten voor PROMs; mediaan van ziekenhuizen voor gecorrigeerde en gepubliceerde scores)

| indicator | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| Diepe wondinfectie binnen 90 dagen | 0.64 | 0.58 | 0.56 | 0.31 |
| Revisie binnen drie jaar (gecorrigeerd) | 1.03 | 1.13 | 0.99 | 1.20 |
| Verbetering volgens patiënt na 12 mnd: EQ-5D index | 0.30 | 0.32 | 0.31 | 0.30 |
| Verbetering volgens patiënt na 12 mnd: EQ-5D thermometer | 8.30 | 8.24 | 8.88 | 8.51 |
| Verbetering volgens patiënt na 12 mnd: NRS-pijn activiteit | 4.94 | 4.89 | 4.80 | 4.84 |
| Verbetering volgens patiënt na 12 mnd: NRS-pijn rust | 3.62 | 3.51 | 3.58 | 3.44 |
| Verbetering volgens patiënt na 12 mnd: OKS | 15.51 | 15.59 | 14.74 | 15.10 |

### Aantal ziekenhuislocaties per oordeel

| verslagjaar | boven_gemiddeld | gemiddeld | gemengd | onder_gemiddeld | geen_data |
|---|---|---|---|---|---|
| 2022 | 10 | 62 | 1 | 12 | 1 |
| 2023 | 8 | 59 | 2 | 18 | 0 |
| 2024 | 7 | 60 | 2 | 18 | 0 |
| 2025 | 15 | 60 | 2 | 11 | 1 |

### Structureel boven gemiddeld (minstens 2 van 2023, 2024, 2025)

| ziekenhuis | jaren |
|---|---|
| Admiraal de Ruyter Ziekenhuis (Goes) | 2023, 2024, 2025 |
| Antonius Ziekenhuis Sneek (Sneek) | 2023, 2025 |
| Erasmus MC (Rotterdam) | 2024, 2025 |
| Frisius MC, locatie Leeuwarden (Leeuwarden) | 2023, 2025 |
| Ijsselland ziekenhuis (Capelle a/d IJssel) | 2024, 2025 |
| Rivas Zorggroep, Beatrixziekenhuis (Gorinchem) | 2023, 2024, 2025 |
| Saxenburgh Medisch Centrum (Hardenberg) | 2023, 2025 |
| Stichting Park Medisch Centrum (Rotterdam) | 2023, 2024 |

### Structureel onder gemiddeld (minstens 2 van 2023, 2024, 2025)

| ziekenhuis | jaren |
|---|---|
| Alrijne Zorggroep (Leiderdorp) | 2023, 2024 |
| Amsterdam UMC - concern (Amsterdam) | 2023, 2024 |
| Bernhoven (Uden) | 2023, 2024 |
| Frisius MC, locatie Heerenveen (Heerenveen) | 2024, 2025 |
| Het Flevoziekenhuis (Almere) | 2023, 2024 |
| Medisch Spectrum Twente (Enschede) | 2023, 2024 |
| OLVG Concern (Amsterdam) | 2023, 2024 |
| Sint Jans Gasthuis (Weert) | 2024, 2025 |
| Stichting Gelre Ziekenhuizen (Apeldoorn) | 2023, 2024 |
| Tergooi MC (Hilversum) | 2023, 2024 |
| UMC Groningen (Groningen) | 2023, 2024 |
| VieCuri Medisch centrum voor NoordLimburg (Venlo) | 2023, 2025 |
| Ziekenhuis Rijnstate (Arnhem) | 2023, 2024, 2025 |

### Verbeterd van 2024 naar 2025

| ziekenhuis | 2024 | 2025 |
|---|---|---|
| Alrijne Zorggroep (Leiderdorp) | onder_gemiddeld | gemiddeld |
| Amsterdam UMC - concern (Amsterdam) | onder_gemiddeld | gemiddeld |
| Antonius Ziekenhuis Sneek (Sneek) | gemiddeld | boven_gemiddeld |
| Bergman Clinics / Bewegen / Naarden (Naarden) | gemiddeld | boven_gemiddeld |
| Bernhoven (Uden) | onder_gemiddeld | gemiddeld |
| Diakonessenhuis Utrecht, Zeist, Doorn (Utrecht) | onder_gemiddeld | gemiddeld |
| Dijklander Ziekenhuis (Hoorn) | gemiddeld | boven_gemiddeld |
| Frisius MC, locatie Leeuwarden (Leeuwarden) | gemiddeld | boven_gemiddeld |
| Groene Hart Ziekenhuis (Gouda) | onder_gemiddeld | gemengd |
| Het Flevoziekenhuis (Almere) | onder_gemiddeld | gemiddeld |
| Maxima Medisch Centrum (Veldhoven) | onder_gemiddeld | gemiddeld |
| Meander Medisch Centrum (Amersfoort) | gemiddeld | boven_gemiddeld |
| Medisch Spectrum Twente (Enschede) | onder_gemiddeld | gemiddeld |
| OLVG Concern (Amsterdam) | onder_gemiddeld | gemiddeld |
| Ommelander Ziekenhuis Groningen (Scheemda) | gemiddeld | boven_gemiddeld |
| Reinier Haga Groep Orthopedisch Centrum B.V. (Zoetermeer) | gemiddeld | boven_gemiddeld |
| Saxenburgh Medisch Centrum (Hardenberg) | gemiddeld | boven_gemiddeld |
| Sint Antonius Ziekenhuis, concern (Nieuwegein) | onder_gemiddeld | gemiddeld |
| Stichting Gelre Ziekenhuizen (Apeldoorn) | onder_gemiddeld | gemiddeld |
| Stichting het van Weel-Bethesda Ziekenhuis, Dirksland (Dirksland) | onder_gemiddeld | gemiddeld |
| Tergooi MC (Hilversum) | onder_gemiddeld | gemengd |
| UMC Groningen (Groningen) | onder_gemiddeld | boven_gemiddeld |
| Ziekenhuis Nij Smellinghe (Drachten) | onder_gemiddeld | gemiddeld |
| Ziekenhuis St Jansdal (Harderwijk) | gemiddeld | boven_gemiddeld |
| ZorgSaam Ziekenhuis (Terneuzen) | gemengd | boven_gemiddeld |

### Verslechterd van 2024 naar 2025

| ziekenhuis | 2024 | 2025 |
|---|---|---|
| Albert Schweitzer Ziekenhuis (Dordrecht) | gemiddeld | onder_gemiddeld |
| Bergman Clinics / Bewegen / Rijswijk (Rijswijk) | gemiddeld | onder_gemiddeld |
| Bergman Clinics / Bewegen / Rotterdam (Rotterdam) | gemiddeld | onder_gemiddeld |
| Deventer Ziekenhuis (Deventer) | gemiddeld | onder_gemiddeld |
| Kliniek ViaSana (Mill) | gemiddeld | onder_gemiddeld |
| Sint Maartenskliniek, concern (Ubbergen) | gemiddeld | onder_gemiddeld |
| Stichting Laurentius Ziekenhuis Roermond (Roermond) | boven_gemiddeld | gemiddeld |
| Stichting Park Medisch Centrum (Rotterdam) | boven_gemiddeld | gemiddeld |
| VieCuri Medisch centrum voor NoordLimburg (Venlo) | gemiddeld | onder_gemiddeld |
| Xpert Clinics Utrecht Janssoniuslaan (Utrecht) | boven_gemiddeld | gemiddeld |
| Ziekenhuis Gelderse Vallei (Ede Gld.) | gemiddeld | onder_gemiddeld |

## Staaroperatie (cataract)

### Landelijk niveau per indicator

(percentages voor uitkomsten; gemiddelde verbetering in punten voor PROMs; mediaan van ziekenhuizen voor gecorrigeerde en gepubliceerde scores)

| indicator | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| Minstens 1 regel beter zien | 95.81 | 95.22 | 94.47 | 94.49 |
| Refractie binnen 0.5 dioptrie van doel |  |  |  | 77.88 |
| Refractie binnen 1 dioptrie van doel | 94.95 | 94.66 | 94.75 |  |

### Aantal ziekenhuislocaties per oordeel

| verslagjaar | boven_gemiddeld | gemiddeld | gemengd | onder_gemiddeld | geen_data |
|---|---|---|---|---|---|
| 2022 | 5 | 71 | 0 | 21 | 3 |
| 2023 | 4 | 76 | 0 | 18 | 4 |
| 2024 | 4 | 69 | 0 | 14 | 1 |
| 2025 | 7 | 78 | 3 | 14 | 8 |

### Structureel boven gemiddeld (minstens 2 van 2023, 2024, 2025)

| ziekenhuis | jaren |
|---|---|
| Bergman Clinics / Ogen / Lelystad (Lelystad) | 2023, 2024 |
| Stichting Eye P. (Driebergen) | 2024, 2025 |
| Ziekenhuis Nij Smellinghe (Drachten) | 2023, 2024 |

### Structureel onder gemiddeld (minstens 2 van 2023, 2024, 2025)

| ziekenhuis | jaren |
|---|---|
| Concernniveau: Stolmed Klinieken (Bergen op Zoom) | 2023, 2024 |
| Maasziekenhuis Pantein (Beugen) | 2024, 2025 |
| Medisch Spectrum Twente (Enschede) | 2023, 2024 |
| Radboud UMC (Nijmegen) | 2023, 2024, 2025 |
| Sint Jans Gasthuis (Weert) | 2023, 2024 |
| Spijkenisse Medisch Centrum (Spijkenisse) | 2023, 2024 |
| Stichting Oog Medisch Centrum Zaandam (Zaandam) | 2023, 2025 |
| UMC Utrecht (Utrecht) | 2024, 2025 |

### Verbeterd van 2024 naar 2025

| ziekenhuis | 2024 | 2025 |
|---|---|---|
| Admiraal de Ruyter Ziekenhuis (Goes) | gemiddeld | boven_gemiddeld |
| Canisius Wilhelmina Ziekenhuis (Nijmegen) | onder_gemiddeld | gemiddeld |
| Concernniveau: Stolmed Klinieken (Bergen op Zoom) | onder_gemiddeld | gemiddeld |
| Dr. Binkhorst Eye Center (Terneuzen) | onder_gemiddeld | gemiddeld |
| Franciscus Concern (Rotterdam) | onder_gemiddeld | gemiddeld |
| Maastricht UMC, Maastricht (Maastricht) | onder_gemiddeld | gemiddeld |
| OLVG Concern (Amsterdam) | gemiddeld | boven_gemiddeld |
| Oog en Welzijn B.V. (DOKKUM) | onder_gemiddeld | gemiddeld |
| Oogcentrum Noordholland B.V. (Heerhugowaard) | onder_gemiddeld | gemiddeld |
| Rivas Zorggroep, Beatrixziekenhuis (Gorinchem) | gemiddeld | boven_gemiddeld |
| Sint Jans Gasthuis (Weert) | onder_gemiddeld | gemiddeld |
| Spijkenisse Medisch Centrum (Spijkenisse) | onder_gemiddeld | gemiddeld |
| Stichting HagaZiekenhuis (Den Haag) | gemiddeld | boven_gemiddeld |
| Wilhelmina Ziekenhuis Assen (Assen) | gemiddeld | boven_gemiddeld |
| Ziekenhuis St Jansdal (Harderwijk) | gemiddeld | boven_gemiddeld |

### Verslechterd van 2024 naar 2025

| ziekenhuis | 2024 | 2025 |
|---|---|---|
| Amphia ziekenhuis (Breda) | gemiddeld | onder_gemiddeld |
| Bergman Clinics / Ogen / Den Bosch (Den Bosch) | gemiddeld | onder_gemiddeld |
| Bergman Clinics / Ogen / Lelystad (Lelystad) | boven_gemiddeld | gemiddeld |
| Diakonessenhuis Utrecht, Zeist, Doorn (Utrecht) | gemiddeld | onder_gemiddeld |
| Dijklander Ziekenhuis (Hoorn) | gemiddeld | onder_gemiddeld |
| Ikazia Ziekenhuis Rotterdam (Rotterdam) | gemiddeld | onder_gemiddeld |
| Oogkliniek Den Haag B.V. (Den Haag) | gemiddeld | onder_gemiddeld |
| Saxenburgh Medisch Centrum (Hardenberg) | gemiddeld | onder_gemiddeld |
| St. Anna Ziekenhuis (Geldrop) | gemiddeld | onder_gemiddeld |
| Stichting Catharina Ziekenhuis (Eindhoven) | gemiddeld | onder_gemiddeld |
| Stichting Laurentius Ziekenhuis Roermond (Roermond) | boven_gemiddeld | gemiddeld |
| Stichting Oogartsenpraktijk Delfland (DELFT) | gemiddeld | onder_gemiddeld |
| Ziekenhuis Nij Smellinghe (Drachten) | boven_gemiddeld | gemiddeld |
