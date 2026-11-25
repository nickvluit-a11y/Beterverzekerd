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

- na zoeken: https://www.zilverenkruis.nl/consumenten/zorgzoeker
- zichtbare tekst: 2,374 tekens
- JSON-antwoorden voor/na zoeken: 0/2

## JSON-antwoorden na het zoeken (grootste eerst)

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

