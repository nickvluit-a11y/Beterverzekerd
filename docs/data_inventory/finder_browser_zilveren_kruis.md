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

Zichtbare knoppen en keuzevelden:

- BUTTON |  |  |  | Zoeken | 
- BUTTON |  | global-header-desktop-top-trigger-1 |  | Verzekeringen | 
- BUTTON |  | global-header-desktop-top-trigger-2 |  | Vergoedingen | 
- BUTTON |  | global-header-desktop-top-trigger-3 |  | Zorg regelen | 
- BUTTON |  | global-header-desktop-top-trigger-4 |  | Betalen | 
- BUTTON |  | global-header-desktop-top-trigger-5 |  | Gezonder leven | 
- BUTTON |  | global-header-desktop-top-trigger-6 |  | Over ons | 
- BUTTON |  | global-header-desktop-top-trigger-7 |  | Contact | 
- BUTTON |  | zorgzoeker-change-search |  | Wijzig zoekopdracht | 
- LABEL |  | Basisverzekering-label |  | Basisverzekering 
Informatie weergeven

Kies je basisverzeke | 
- BUTTON |  | popover-Basisverzekering-trigger |  | Informatie weergeven | 
- BUTTON | combobox | Basisverzekering-button |  | Kies uw basisverzekering | 
- LABEL |  | zorgzoeker-jaar |  | Jaar | 
- INPUT |  | zorgzoeker-jaar-2025 | zorgzoeker-jaar | 2025 | 
- LABEL |  |  |  | 2025 | 
- INPUT |  | zorgzoeker-jaar-2026 | zorgzoeker-jaar | 2026 | 
- LABEL |  |  |  | 2026 | 
- INPUT |  | zorgzoeker-jaar-2027 | zorgzoeker-jaar | 2027 | 
- LABEL |  |  |  | 2027 | 
- INPUT |  | status_gecontracteerd | zorgzoeker-contractstatus | Contract: vergoed | 
- LABEL |  |  |  | Contract: vergoed | 
- INPUT |  | status_in_onderhandeling | zorgzoeker-contractstatus | Nog geen contract: wel vergoed | 
- LABEL |  |  |  | Nog geen contract: wel vergoed | 
- INPUT |  | status_in_onderhandeling | zorgzoeker-contractstatus | Nog geen contract: een deel niet vergoed | 
- LABEL |  |  |  | Nog geen contract: een deel niet vergoed | 
- INPUT |  | status_vervallen | zorgzoeker-contractstatus | Geen contract: een deel niet vergoed | 
- LABEL |  |  |  | Geen contract: een deel niet vergoed | 
- LABEL |  | select-Basisverzekering-label |  | Je basisverzekering | 
- BUTTON | combobox | select-Basisverzekering-button |  | Selecteer | 
- BUTTON |  |  |  | Klaar | 
- BUTTON |  | buttonJa |  | Ja | 
- BUTTON |  | buttonNee |  | Nee | 

- opties onder #select-Basisverzekering-button: Basis Exclusief; Basis Start; Basis Start (voorheen Basis Budget); Basis Zeker; ZieZo Basis
- gekozen: Basis Zeker

- na zoeken: https://www.zilverenkruis.nl/consumenten/zorgzoeker/zoekresultaten
- zichtbare tekst: 2,539 tekens
- JSON-antwoorden voor/na zoeken: 0/6

## JSON-antwoorden na het zoeken (grootste eerst)

Volledige data van de grootste aanroep: finder_browser_zilveren_kruis.json

### POST 200 https://www.zilverenkruis.nl/clientcontroller/zorgzoekerclient/getzorgaanbieders (69,290 tekens)

Verzonden:
```
{"Zorgtype":"1861","LocatieId":"194117","Basisverzekering":"100","Peildatum":"2027-01-01T00:00:00.000Z"}
```
```
{"AantalResultaten":75,"Tussenvragen":["vraag polistype"],"Zoektermen":{"Locatie":null,"LocatieId":194117,"Instelling":"","Zorgtype":"1861","Peildatum":"2027-01-01T00:00:00Z","Basisverzekering":"100"},"VertrekLocatieLatitude":52.08602049,"VertrekLocatieLongitude":5.17960178,"Resultaten":[{"Contracten":[{"StatusOmschrijving":"Nog geen contract: een deel niet vergoed","Zorgtype":"","Toelichting":"Nog geen contract: een deel niet vergoed","TypeLocatie":2,"Begindatum":"2027-01-01T00:00:00Z","Einddatum":"2027-12-31T00:00:00Z","TypeContractVergoeding":"GedeeltelijkVergoed","Uitsluitingen":null,"Insluitingen":null,"Kenmerken":null,"Patientenstop":"","IsPlafondafspraakAanwezig":true,"IsPlafondafspraakBereikt":false,"RelativeURL":""}],"Meldingen":null,"IsChristelijk":false,"IsPluspraktijk":false,"RelativeURL":"/umc-utrecht-loc-azu-3584cx/ae5b583a-31c9-4f27-9abf-c2391cb72d17","Naam":"UMC Utrecht, loc. AZU","AGBNummer":6020602,"LocatieId":"ae5b583a-31c9-4f27-9abf-c2391cb72d17","Website":"http://www.umcutrecht.nl","Adres":{"Straat":"HEIDELBERGLN","Postcode":"3584CX","Huisnummer":"100","Plaats":"UTRECHT","Land":"","Afstand":"","Latitude":52.08602049,"Longitude":5.17960178}},{"Contracten":[{"StatusOmschrijving":"Nog geen contract: een deel niet vergoed","Zorgtype":"","Toelichting":"Nog geen contract: een deel niet vergoed","TypeLocatie":2,"Begindatum":"2027-01-01T00:00:00Z","Einddatum":"2027-12-31T00:00:00Z","TypeContractVergoeding":"GedeeltelijkVergoed","Uitsluitingen":null,"Insluitingen":null,"Kenmerken":null,"Patientenstop":"","IsPlafondafspraakAanwezig":true,"IsPlafondafspraakBereikt":false,"RelativeURL":""}],"Meldingen":null,"IsChristelijk":false,"IsPluspraktijk":false,"RelativeURL":"/umc-utrecht-loc-wilhelmina-kinderziekenhuis-wkz-3584ea/e688b8d3-3458-49e8-bf79-184dcb14d6d3","Naam":"UMC Utrecht, loc. Wilhelmina Kinderziekenhuis (WKZ)","AGBNummer":6020602,"LocatieId":"e688b8d3-3458-49e8-bf79-184dcb14d6d3","Website":"http://www.umcutrecht.nl","Adres":{"Straat":"LUNDLN","Postcode":"3584EA","Huisnummer":"6","Plaats":"UTRECHT","Land":"","Afstand":"0,4 km","Latitude":52.08942212,"Longitude":5.18097449}},{"Contracten":[{"StatusOmschrijving":"Contract: vergoed","Zorgtype":"","Toelichting":"Contract: vergoed","TypeLocatie":2,"Begindatum":"2026-01-01T00:00:00Z","Einddatum":"2028-12-31T00:00:00Z","TypeContractVergoeding":"Vergoed","Uitsluitingen":null,"Insluitingen":null,"Kenmerken":null,"Patientenstop":"","IsPlafondafspraakAanwezig":false,"IsPlafondafspraakBereikt":false,"RelativeURL":""}],"Meldingen":null,"IsChristelijk":false,"IsPluspraktijk":false,"RelativeURL":"/prinses-maxima-centrum-voor-kinderoncologie-3584cs/d76e6580-2945-4a09-b6e8-fe0ea93f497b","Naam":"Prinses Maxima Centrum voor Kinderoncologie","AGBNummer":6080801,"LocatieId":"d76e6580-2945-4a09-b6e8-fe0ea93f497b","Website":"http://www.prinsesmaximacentrum.nl/","Adres":{"Straat":"HEIDELBERGLN","Postcode":"3584CS","Huisnummer":"25","Plaats":"UTRECHT","Land":"","Afstand":"0,5 km","Latitude":52.08988376,"L
```

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

