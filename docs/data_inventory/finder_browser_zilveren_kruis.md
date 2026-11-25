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
- invullen Ziekenhuis: TimeoutError

- na zoeken: https://www.zilverenkruis.nl/consumenten/zorgzoeker
- zichtbare tekst: 2,353 tekens
- JSON-antwoorden voor/na zoeken: 0/1

## JSON-antwoorden na het zoeken (grootste eerst)

### POST 200 https://www.zilverenkruis.nl/clientcontroller/zorgzoekerclient/getautofilllocatie (126 tekens)

Verzonden:
```
{"ZoekstringLocatie":"3584CX"}
```
```
{"isSucces":true,"options":[{"id":"194117","label":"3584CX UTRECHT","value":"3584CX UTRECHT","category":null,"subtext":null}]}
```

