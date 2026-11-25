# Zorgzoeker zilveren_kruis (browser-verkenning 2026-11-25)

- start: https://www.zilverenkruis.nl/consumenten/zorgzoeker
- zoekpagina: https://www.zilverenkruis.nl/consumenten/zorgzoeker

## Invoervelden

- ch-main-nav-search-input Zoeken  Zoekterm (INPUT/search)
- ch-mobile-main-nav-search-input Zoeken  Zoekterm (INPUT/search)
- autofill-Zorgtype-input Bijvoorbeeld: fysiotherapie  Welke zorg * (INPUT/text)
- autofill-Locatie-input Bijvoorbeeld: Leiden  Plaats of postcode 
Informatie weergeven
Plaats of postcode

Vul een postcode in voor een nauwkeuriger resultaat (INPUT/text)
- autofill-Instelling-input Bijvoorbeeld: UMC  Naam van organisatie of zorgverlener (INPUT/text)
- #autofill-Zorgtype-input: gekozen suggestie voor Ziekenhuis
- #autofill-Locatie-input: gekozen suggestie voor 3584 CX
- zoekknoppen gevonden: 2

- na zoeken: https://www.zilverenkruis.nl/consumenten/zorgzoeker/zoekresultaten
- zichtbare tekst: 1,481 tekens
- JSON-antwoorden voor/na zoeken: 0/5

## JSON-antwoorden na het zoeken (grootste eerst)

Volledige data van de grootste aanroep: finder_browser_zilveren_kruis.json

### GET 200 https://www.zilverenkruis.nl/clientcontroller/zorgzoekerclient/getcontractstatusexplanations (3,923 tekens)

```
{"Nog geen contract: wel vergoed":{"Text":"<ul>\n    <li>Met deze zorgverlener zijn we nog in gesprek met als doel afspraken te maken.</li>\n    <li>Wel vergoeden we je zorg volgens je&nbsp;<a rel=\"noopener noreferrer\" href=\"https://www.zilverenkruis.nl/consumenten/vergoedingen\">polisvoorwaarden</a>. Net als bij een zorgverlener met contract.</li>\n    <li>Mogelijk maken we met deze zorgverlener een afspraak over het maximale bedrag dat de zorgverlener per jaar bij ons in rekening mag brengen. Dit noemen we een <a href=\"/consumenten/zorg-regelen/omzetplafonds\">omzetplafond</a>.&nbsp;</li>\n<li>Heeft de zorgverlener het omzetplafond bereikt voor dat jaar? Dan kun je voor een nieuwe behandeling in dit jaar misschien niet meer naar deze zorgverlener.</li>\n</ul>","WithLimitationsText":null,"TypeContractVergoeding":"Vergoed"},"Nog geen contract: een deel niet vergoed":{"Text":"<ul>\n    <li>Met deze zorgverlener zijn we nog in gesprek met als doel afspraken te maken. Hebben we afspraken gemaakt? Dan werken we de Zorgzoeker bij.</li>\n    <li>Zolang er nog geen contract is vergoeden we je zorg volgens je&nbsp;<a rel=\"noopener noreferrer\" href=\"https://www.zilverenkruis.nl/consumenten/vergoedingen/niet-gecontracteerde-zorg\">polisvoorwaarden</a> voor niet-gecontracteerde zorg. Dit betekent dat je een deel van de rekening zelf betaalt.</li>\n    <li>Was je in 2026 in behandeling bij deze zorgverlener? En hadden we in 2026 een contract met deze zorgverlener, maar in 2027 niet? Als je in 2026 klant bij ons bent en in 2027 klant bij ons blijft, geldt een overgangsregeling van maximaal 1 jaar voor een behandeling die doorloopt in 2027. We vergoeden deze zorg volgens je&nbsp;<a rel=\"noopener noreferrer\" href=\"https://www.zilverenkruis.nl/consumenten/vergoedingen\">polisvoorwaarden</a>. Net als bij een zorgverlener met contract.</li>\n</ul>\n<div>&nbsp;</div>","WithLimitationsText":null,"TypeContractVergoeding":"GedeeltelijkVergoed"},"Geen contract: een deel niet vergoed":{"Text":"<ul>\n    <li>Met deze zorgverlener hebben we geen afspraken gemaakt.</li>\n    <li>We vergoeden je zorg volgens je&nbsp;polisvoorwaarden voor <a href=\"/consumenten/vergoedingen/niet-gecontracteerde-zorg\">niet-gecontracteerde zorg</a>. Dit betekent dat je een deel van de rekening zelf betaalt.</li>\n    <li>Was je in 2026 in behandeling bij deze zorgverlener? En hadden we in 2026 een contract met deze zorgverlener, maar in 2027 niet? Als je in 2026 klant bij ons bent en in 2027 klant bij ons blijft, geldt een overgangsregeling van maximaal 1 jaar voor een behandeling die doorloopt in 2027. We vergoeden deze zorg volgens je&nbsp;<a rel=\"noopener noreferrer\" href=\"https://www.zilverenkruis.nl/consumenten/vergoedingen\">polisvoorwaarden</a>. Net als bij een zorgverlener met contract</li>\n</ul>\n<div>&nbsp;</div>","WithLimitationsText":null,"TypeContractVergoeding":"NietVergoed"},"Contract: vergoed":{"Text":"<ul>\n    <li>Met deze zorgverlener hebben we afspraken gemaa
```

### GET 200 https://www.zilverenkruis.nl/clientcontroller/zorgzoekerclient/getpatientstopnotifications (565 tekens)

```
[{"Code":"CODE1","Title":"Zorgverlener is tijdelijk gesloten (CODE1)","Description":"I.v.m personeelskrapte is deze zorgverlener in maanden Juli en Augustus gesloten."},{"Code":"CODE2","Title":"Zorgverlener is permanent gesloten (CODE2)","Description":"Deze zorgverlener is wegens betalingsproblemen gesloten vanaf Maart 2025"},{"Code":"CodeRood","Title":"Deze zorgverlener is tijdelijk gesloten","Description":"Vanwege code rood neemt deze zorgverlener tijdelijk geen nieuwe patiënten aan. Zie https://www.zilverenkruis.nl/consumenten/zorg-regelen/omzetplafonds"}]
```

### POST 200 https://www.zilverenkruis.nl/clientcontroller/zorgzoekerclient/getzorgaanbieders (423 tekens)

Verzonden:
```
{"Zorgtype":"1861","LocatieId":"194117","Peildatum":"2027-01-01T00:00:00.000Z"}
```
```
{"AantalResultaten":0,"Tussenvragen":["vraag polistype"],"Zoektermen":{"Locatie":null,"LocatieId":194117,"Instelling":"","Zorgtype":"1861","Peildatum":"2027-01-01T00:00:00Z","Basisverzekering":null},"VertrekLocatieLatitude":0.0,"VertrekLocatieLongitude":0.0,"Resultaten":null,"Meldingen":null,"GebruiktZorgtype":"Ziekenhuis","GebruiktZorgtypeId":"1861","IsSucces":true,"ErrorCode":null,"LoginAlsKlantSessieNotActive":false}
```

### POST 200 https://www.zilverenkruis.nl/clientcontroller/zorgzoekerclient/getautofillzorgtype (401 tekens)

Verzonden:
```
{"ZoekstringZorgtype":"Ziekenhuis"}
```
```
{"isSucces":true,"options":[{"id":"2012","label":"Ziekenhuispsychiatrie","value":"Ziekenhuispsychiatrie","category":"Geestelijke gezondheidszorg","subtext":null},{"id":"1861","label":"Ziekenhuis","value":"Ziekenhuis","category":"Ziekenhuis","subtext":null},{"id":"2067","label":"Ziekenhuis in het buitenland","value":"Ziekenhuis in het buitenland","category":"Zorg in het buitenland","subtext":null}]}
```

### POST 200 https://www.zilverenkruis.nl/clientcontroller/zorgzoekerclient/getautofilllocatie (126 tekens)

Verzonden:
```
{"ZoekstringLocatie":"3584CX"}
```
```
{"isSucces":true,"options":[{"id":"194117","label":"3584CX UTRECHT","value":"3584CX UTRECHT","category":null,"subtext":null}]}
```

