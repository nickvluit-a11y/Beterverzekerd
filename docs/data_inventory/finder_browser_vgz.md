# Zorgzoeker vgz (browser-verkenning 2026-11-25)

- start: https://www.vgz.nl/zorg-regelen/zorgzoeker
- zoekpagina: https://www.vgz.nl/zorg-regelen/zorgzoeker#/filter

## Invoervelden

- search Ik ben op zoek naar... (INPUT/search)
- zoekterm zoekterm Welke zorg(verlener) zoek je?  Welke zorg(verlener) zoek je? (INPUT/text)
- locatie locatie Wat is je postcode of plaats?  In welke omgeving zoekt u? (INPUT/text)
- afstand afstand   afstand (SELECT/select-one)
- vendor-search-handler vendor-search-handler Zoeken… Zoeken in cookielijsten (INPUT/text)
- input[name=zoekterm] (Ziekenhuis): TimeoutError: Locator.click: Timeout 3000ms exceeded.
Call log:
  - waiting for get_by_role("option").visible.first
    - locator resolved to <li tabindex="-1" role
- input[name=locatie]: ingevuld 3584 CX

- na zoeken: https://www.vgz.nl/zorg-regelen/zorgzoeker/zoekresultaten#/resultaten?zorgsoortId=015&locatie=3584%20CX&straal=50000&jaar=2027&synoniem=Ziekenhuis&uniqueId=2027_185658_6
- zichtbare tekst: 10,269 tekens
- JSON-antwoorden voor/na zoeken: 17/29

## JSON-antwoorden na het zoeken (grootste eerst)

Volledige data van de grootste aanroep: finder_browser_vgz.json

### GET 200 https://api.vgz.nl/zorgzoeker/api/v2/zorgaanbieder/zoekopzorgsoort/vgz/2027/015?contractStatus=6&gebruikVerzorgingsgebieden=false&sortByGoodPractice=true&initieleZorgsoortCode=015&landCode=NL&postcode=3584%20CX&zoekRadius=50&sortering=AfstandOplopend&skip=0&take=25&soortLocatie=3 (211,931 tekens)

```
{"gebruikerslocatie":{"lengtegraad":5.16552545,"breedtegraad":52.0842699},"facetering":{"aantallen":{"nietGecontracteerd":304,"inOnderhandeling":287,"gecontracteerd":60},"contractSubstatus":{"gecontracteerd":26,"gecontracteerdZKPBereikt":0,"gecontracteerdZonderDLP":34,"inOnderhandeling":287,"inOnderhandelingAltijdVergoed":0,"inOnderhandelingTijdensOnderhandelingVergoed":0,"erkend":0,"nietGecontracteerd":299,"uitsluiting":5},"zorgsoorten":[{"code":"015.0100","naam":"Allergologie","zorgsoortType":"careType","aantalResultaten":20,"heeftResultaten":true},{"code":"015.0200","naam":"Cardiologie","zorgsoortType":"careType","aantalResultaten":77,"heeftResultaten":true},{"code":"015.0600","naam":"Chirurgie","zorgsoortType":"careType","aantalResultaten":114,"heeftResultaten":true},{"code":"015.0300","naam":"Dermatologie","zorgsoortType":"careType","aantalResultaten":139,"heeftResultaten":true},{"code":"015.0400","naam":"Geriatrie","zorgsoortType":"careType","aantalResultaten":48,"heeftResultaten":true},{"code":"015.0500","naam":"Gynaecologie - Verloskunde","zorgsoortType":"careType","aantalResultaten":84,"heeftResultaten":true},{"code":"015.2900","naam":"Hyperbare geneeskunde","zorgsoortType":"careType","aantalResultaten":3,"heeftResultaten":true},{"code":"015.0700","naam":"Inwendige geneeskunde","zorgsoortType":"careType","aantalResultaten":80,"heeftResultaten":true},{"code":"015.0800","naam":"Kaakchirurgie","zorgsoortType":"careType","aantalResultaten":44,"heeftResultaten":true},{"code":"015.0900","naam":"Kindergeneeskunde","zorgsoortType":"careType","aantalResultaten":56,"heeftResultaten":true},{"code":"015.1000","naam":"KNO","zorgsoortType":"careType","aantalResultaten":109,"heeftResultaten":true},{"code":"015.1100","naam":"Longgeneeskunde","zorgsoortType":"careType","aantalResultaten":55,"heeftResultaten":true},{"code":"015.1200","naam":"Maag- darm- en leverziekten","zorgsoortType":"careType","aantalResultaten":69,"heeftResultaten":true},{"code":"015.1300","naam":"Neurochirurgie","zorgsoortType":"careType","aantalResultaten":38,"heeftResultaten":true},{"code":"015.1400","naam":"Neurologie","zorgsoortType":"careType","aantalResultaten":106,"heeftResultaten":true},{"code":"015.1500","naam":"Oncologie","zorgsoortType":"careType","aantalResultaten":38,"heeftResultaten":true},{"code":"015.1600","naam":"Oogheelkunde","zorgsoortType":"careType","aantalResultaten":77,"heeftResultaten":true},{"code":"015.1700","naam":"Orthopedie","zorgsoortType":"careType","aantalResultaten":90,"heeftResultaten":true},{"code":"015.2500","naam":"Pijnbestrijding - Anesthesiologie","zorgsoortType":"careType","aantalResultaten":87,"heeftResultaten":true},{"code":"015.1800","naam":"Plastische chirurgie","zorgsoortType":"careType","aantalResultaten":97,"heeftResultaten":true},{"code":"015.1900","naam":"Psychiatrie","zorgsoortType":"careType","aantalResultaten":20,"heeftResultaten":true},{"code":"015.2800","naam":"Radiotherapie","zorgsoortType":"careType","aantalResultaten":14,"heeft
```

### GET 200 https://vgz1.expoints.nl/m/external-configs/18da370d-357c-44d8-9e1a-f7b4259f2a33.json (171,882 tekens)

```
{"id":"18da370d-357c-44d8-9e1a-f7b4259f2a33","name":"VGZ Online","daysBlockade":90,"disableBlockade":false,"disableLocationMonitor":false,"externalQuestionnaires":[{"id":"6dafd2ee-f23d-4e74-9e51-01156162bb5b","name":"OO - Overgang thema - CES - LMT AH - VGZ","showPoweredByExpoints":false,"frameType":1,"frameLoaderType":0,"frameOpenType":1,"frameTitle":"Geef je mening","autoResizeHeight":true,"autoResizeMaximumHeight":550,"autoResizeMinimumHeight":150,"height":null,"width":"350px","setBlockAtFinish":false,"ignoreBlock":false,"clickOutsideToClose":true,"selector":null,"poweredByExpointsHref":null,"poweredByExpointsFileName":null,"autoCloseAtFinishTimeoutInSeconds":null,"entranceAnimation":null,"exitAnimation":null,"iframeDescription":"Geef hier je feedback","buttonCustomStyle":null,"frameCustomStyle":null,"loadIconAriaLabel":null,"externalButton":null,"externalFrame":{"id":"8e562811-40ac-4b30-91c5-43d1c966ca52","frameSettings":[{"key":5,"value":"none","display":"border","group":"Border instellingen","filterProperty":"","filterValue":0},{"key":6,"value":"12px","display":"border-radius","group":"Border instellingen","filterProperty":"","filterValue":0},{"key":16,"value":"true","display":"","group":"Border instellingen","filterProperty":"","filterValue":0},{"key":28,"value":"35px","display":"$frame-footer-height","group":"Powered by Expoints footer","filterProperty":"","filterValue":2},{"key":35,"value":"unset","display":"left","group":"Desktop/tablet","filterProperty":"","filterValue":0},{"key":36,"value":"120px","display":"right","group":"Desktop/tablet","filterProperty":"","filterValue":0},{"key":37,"value":"0","display":"bottom","group":"Desktop/tablet","filterProperty":"","filterValue":0},{"key":38,"value":"unset","display":"top","group":"Desktop/tablet","filterProperty":"","filterValue":0},{"key":39,"value":"unset","display":"left","group":"Mobiel","filterProperty":"","filterValue":0},{"key":40,"value":"0","display":"right","group":"Mobiel","filterProperty":"","filterValue":0},{"key":41,"value":"0","display":"bottom","group":"Mobiel","filterProperty":"","filterValue":0},{"key":42,"value":"unset","display":"top","group":"Mobiel","filterProperty":"","filterValue":0},{"key":45,"value":"Sluiten","display":"","group":"Afgerond sluit knop","filterProperty":"","filterValue":null},{"key":46,"value":"Sluiten","display":"","group":"Header instellingen","filterProperty":"","filterValue":null},{"key":47,"value":"none","display":"","group":"Specific feedback element selection","filterProperty":"","filterValue":0},{"key":48,"value":"0","display":"","group":"Specific feedback element selection","filterProperty":"","filterValue":0}]},"targets":[{"type":8,"operator":3,"invertOperator":false,"value":"/gezond-leven/de-overgang","startDate":null,"endDate":null,"devices":[]}],"triggers":[{"id":641,"type":1,"value":"10","delay":null}]},{"id":"270802b1-68aa-46b9-ae5d-072d3cc6a7f9","name":"OO - Zwangerschap thema - CES - LMT AH - VGZ","showPoweredByExpoints":false,"fra
```

### GET 200 https://vgz2.expoints.nl/m/external-configs/d0b2688e-ce3d-4be6-9d22-6b73d2e16042.json (32,097 tekens)

```
{"id":"d0b2688e-ce3d-4be6-9d22-6b73d2e16042","name":"VGZ Online","daysBlockade":90,"disableBlockade":false,"disableLocationMonitor":false,"externalQuestionnaires":[{"id":"b856b443-6a8d-4762-a9b7-0510627cd516","name":"KMT-IAV - Pop up wachttijd VGZ - Annabel Koppes - 1023","showPoweredByExpoints":false,"frameType":0,"frameLoaderType":0,"frameOpenType":0,"frameTitle":"Gelijk oversteken keuzehulp","autoResizeHeight":true,"autoResizeMaximumHeight":500,"autoResizeMinimumHeight":250,"height":null,"width":"650px","setBlockAtFinish":false,"ignoreBlock":true,"clickOutsideToClose":false,"selector":null,"poweredByExpointsHref":null,"poweredByExpointsFileName":null,"autoCloseAtFinishTimeoutInSeconds":null,"entranceAnimation":null,"exitAnimation":null,"iframeDescription":"","buttonCustomStyle":null,"frameCustomStyle":null,"loadIconAriaLabel":null,"externalButton":null,"externalFrame":{"id":"f5b808e6-3445-453e-8198-ae4f76f08b96","frameSettings":[{"key":5,"value":"none","display":"border","group":"Border instellingen","filterProperty":"","filterValue":0},{"key":6,"value":"12px","display":"border-radius","group":"Border instellingen","filterProperty":"","filterValue":0},{"key":16,"value":"true","display":"","group":"Border instellingen","filterProperty":"","filterValue":0},{"key":28,"value":"35px","display":"$frame-footer-height","group":"Powered by Expoints footer","filterProperty":"","filterValue":2},{"key":35,"value":"unset","display":"left","group":"Desktop/tablet","filterProperty":"","filterValue":0},{"key":36,"value":"0","display":"right","group":"Desktop/tablet","filterProperty":"","filterValue":0},{"key":37,"value":"0","display":"bottom","group":"Desktop/tablet","filterProperty":"","filterValue":0},{"key":38,"value":"unset","display":"top","group":"Desktop/tablet","filterProperty":"","filterValue":0},{"key":39,"value":"unset","display":"left","group":"Mobiel","filterProperty":"","filterValue":0},{"key":40,"value":"0","display":"right","group":"Mobiel","filterProperty":"","filterValue":0},{"key":41,"value":"0","display":"bottom","group":"Mobiel","filterProperty":"","filterValue":0},{"key":42,"value":"unset","display":"top","group":"Mobiel","filterProperty":"","filterValue":0},{"key":45,"value":"Sluiten","display":"","group":"Afgerond sluit knop","filterProperty":"","filterValue":null},{"key":46,"value":"Sluiten","display":"","group":"Header instellingen","filterProperty":"","filterValue":null},{"key":47,"value":"none","display":"","group":"Specific feedback element selection","filterProperty":"","filterValue":0},{"key":48,"value":"0","display":"","group":"Specific feedback element selection","filterProperty":"","filterValue":0}]},"targets":[],"triggers":[{"id":32,"type":0,"value":"Wachttijd_Tool_VGZ","delay":null}]},{"id":"4ff37f59-01af-4c03-baa8-4c055f4f40aa","name":"KMT GV Therapieland_C","showPoweredByExpoints":false,"frameType":0,"frameLoaderType":0,"frameOpenType":1,"frameTitle":null,"autoResizeHeight":false,"autoResizeMaximumHeight":null,"autoResize
```

### GET 200 https://api.vgz.nl/zorgzoeker/api/v2/resource/vgz (22,532 tekens)

```
{"nieuwe-contractstatussen":"","contractstatus.gecontracteerd":"<p><strong>Contract: vergoed</strong></p>","contractstatus.toelichting.gecontracteerd":"<p>Met deze zorgverlener hebben we afspraken gemaakt. </p>\n<p>We vergoeden je zorg volledig volgens jouw verzekeringsvoorwaarden. Voor sommige zorg betaal je wel eigen risico en/of eigen bijdrage.</p>","contractstatus.gecontracteerdzonderdlp":"<p><strong>Contract: vergoed</strong><br />Let op: hier is een omzetplafond</p>","contractstatus.toelichting.gecontracteerdzonderdlp":"<p>Met deze zorgverlener hebben we afspraken gemaakt. We vergoeden je zorg volledig volgens jouw verzekeringsvoorwaarden. Voor de meeste zorg betaal je wel eigen risico en/of eigen bijdrage.</p>\n<p><strong>Afspraken over de zorg<br />\n</strong>Wij hebben met deze zorgaanbieder een afspraak gemaakt over het maximale bedrag dat de zorgaanbieder per jaar bij ons in rekening mag brengen. Dit noemen we een <a rel=\"noopener noreferrer\" href=\"https://www.vgz.nl/zorg-regelen/zorgzoeker/omzetplafonds\" target=\"_blank\">omzetplafond</a>. Heeft de zorgaanbieder het omzetplafond bereikt voor dat jaar? Dan kun je voor een nieuwe behandeling misschien niet meer naar deze zorgaanbieder.</p>\n<p><strong>Ziekenhuiszorg<br />\n</strong>Als het omzetplafond bereikt is, zie je dit terug in de Zorgzoeker.</p>\n<ul>\n    <li>Heb je een naturapolis en heb je een nieuwe behandeling nodig? Dan kan het zijn dat je niet bij deze zorgverlener terecht kunt. Voor spoedgevallen en bevallingen kun je altijd in ieder ziekenhuis terecht.&nbsp;</li>\n    <li>Heb je een combinatiepolis? Dan vergoeden we jouw behandeling bij dit ziekenhuis altijd. Ook als het omzetplafond bereikt is.</li>\n</ul>\n<p><strong><br />\nGeestelijke gezondheidszorg (ggz)<br />\n</strong>Heb je een verwijzing van je huisarts naar een zorgverlener, maar geeft deze aan dat het omzetplafond bereikt is? Dan kun je voor een nieuwe behandeling niet meer bij deze zorgverlener terecht.</p>\n<p><strong>Hulp bij het vinden van een zorgverlener<br />\n</strong>Onze zorgadviseurs helpen je graag om een passende zorgverlener in de buurt te vinden. Bel onze zorgadviseurs op telefoonnummer 088 - 131 16 11.</p>","contractstatus.gecontracteerdzkpbereikt":"<p><strong>Contract: vergoed</strong><br />\n<strong>Let op: het omzetplafond is bereikt</strong></p>","contractstatus.toelichting.gecontracteerdzkpbereikt":"<p>Met deze zorgverlener hebben we afspraken gemaakt. We vergoeden je zorg volledig volgens jouw verzekeringsvoorwaarden. Voor sommige zorg betaal je wel eigen risico en/of eigen bijdrage.</p>\n<p><strong>Omzetplafond bereikt<br />\n</strong>Bij deze zorgverlener kun je dit jaar niet meer terecht zorg. Het <a rel=\"noopener noreferrer\" href=\"https://www.vgz.nl/zorg-regelen/zorgzoeker/omzetplafonds\" target=\"_blank\">omzetplafond</a> is bereikt. Voor spoedgevallen en bevallingen kun je altijd terecht.</p>\n<ul>\n    <li>Heb je een naturapolis? Kijk in onze Zorgzoeker welke zorgverleners 
```

### POST 200 https://api.vgz.nl/zorgzoeker/api/v2/zorgkaart/waarderingen (7,134 tekens)

Verzonden:
```
[{"agbCode":"06020602","postcode":"3584CX","huisnummer":"100"},{"agbCode":"06020602","postcode":"3584EA","huisnummer":"6"},{"agbCode":"06080801","postcode":"3584CS","huisnummer":"25"},{"agbCode":"71090770","postcode":"3583TM","huisnummer":"10"},{"agbCode":"22220142","postcode":"3584AA","huisnummer":"379"},{"agbCode":"06010618","postcode":"3582KE","huisnummer":"1"},{"agbCode":"22220012","postcode":"3581CN","huisnummer":"10"},{"agbCode":"22220012","postcode":"3581CN","huisnummer":"10"},{"agbCode":"22220121","postcode":"3511MJ","huisnummer":"600"},{"agbCode":"22220815","postcode":"3706BR","huisnummer":"21"},{"agbCode":"71265993","postcode":"3511EC","huisnummer":"18"},{"agbCode":"06010620","postcode":"3562CN","huisnummer":"6"},{"agbCode":"22220391","postcode":"3526GV","huisnummer":"6"},{"agbCode":"22220815","postcode":"3528AH","huisnummer":"71"},{"agbCode":"22220815","postcode":"3528BJ","huisnummer":"75"},{"agbCode":"22221917","postcode":"3735ME","huisnummer":"14"},{"agbCode":"71128888","postcode":"3735ME","huisnummer":"14"},{"agbCode":"22220336","postcode":"3735ME","huisnummer":"14"},{"agbCode":"06010620","postcode":"3994VZ","huisnummer":"2"},{"agbCode":"71091492","postcode":"3705LZ","huisnummer":"42"},{"agbCode":"22220815","postcode":"3705LZ","huisnummer":"42"}]
```
```
[{"zorgaanbieder":{"agbCode":"06020602","postcode":"3584CX","huisnummer":"100"},"waardering":{"aantalWaarderingen":"85","scoreGemiddeld":8,"zorgaanbiederUrl":"https://www.zorgkaartnederland.nl/zorginstelling/ziekenhuis-umc-utrecht-locatie-heidelberglaan-utrecht-243812","opmerking":null,"zorgKaartNLId":"243812","waardeerURL":"https://www.zorgkaartnederland.nl/zorginstelling/ziekenhuis-umc-utrecht-locatie-heidelberglaan-utrecht-243812/waardeer"}},{"zorgaanbieder":{"agbCode":"06020602","postcode":"3584EA","huisnummer":"6"},"waardering":{"aantalWaarderingen":"13","scoreGemiddeld":6.8,"zorgaanbiederUrl":"https://www.zorgkaartnederland.nl/zorginstelling/ziekenhuis-umc-utrecht-wilhelmina-kinderziekenhuis-utrecht-243813","opmerking":"Deze zorginstelling heeft te weinig waarderingen. Vanaf 30 waarderingen geeft het cijfer een betrouwbaar beeld.","zorgKaartNLId":"243813","waardeerURL":"https://www.zorgkaartnederland.nl/zorginstelling/ziekenhuis-umc-utrecht-wilhelmina-kinderziekenhuis-utrecht-243813/waardeer"}},{"zorgaanbieder":{"agbCode":"06080801","postcode":"3584CS","huisnummer":"25"},"waardering":{"aantalWaarderingen":"3","scoreGemiddeld":9.8,"zorgaanbiederUrl":"https://www.zorgkaartnederland.nl/zorginstelling/kankercentrum-prinses-maxima-centrum-voor-kinderoncologie-utrecht-3055831","opmerking":"Deze zorginstelling heeft te weinig waarderingen. Vanaf 30 waarderingen geeft het cijfer een betrouwbaar beeld.","zorgKaartNLId":"3055831","waardeerURL":"https://www.zorgkaartnederland.nl/zorginstelling/kankercentrum-prinses-maxima-centrum-voor-kinderoncologie-utrecht-3055831/waardeer"}},{"zorgaanbieder":{"agbCode":"71090770","postcode":"3583TM","huisnummer":"10"},"waardering":{"aantalWaarderingen":"15","scoreGemiddeld":8.4,"zorgaanbiederUrl":"https://www.zorgkaartnederland.nl/zorginstelling/revalidatiecentrum-de-hoogstraat-revalidatie-utrecht-111234","opmerking":"Deze zorginstelling heeft te weinig waarderingen. Vanaf 30 waarderingen geeft het cijfer een betrouwbaar beeld.","zorgKaartNLId":"111234","waardeerURL":"https://www.zorgkaartnederland.nl/zorginstelling/revalidatiecentrum-de-hoogstraat-revalidatie-utrecht-111234/waardeer"}},{"zorgaanbieder":{"agbCode":"22220142","postcode":"3584AA","huisnummer":"379"},"waardering":{"aantalWaarderingen":"856","scoreGemiddeld":8.9,"zorgaanbiederUrl":"https://www.zorgkaartnederland.nl/zorginstelling/cardiologiecentrum-cardiologie-centrum-utrecht-utrecht-3029532","opmerking":null,"zorgKaartNLId":"3029532","waardeerURL":"https://www.zorgkaartnederland.nl/zorginstelling/cardiologiecentrum-cardiologie-centrum-utrecht-utrecht-3029532/waardeer"}},{"zorgaanbieder":{"agbCode":"06010618","postcode":"3582KE","huisnummer":"1"},"waardering":{"aantalWaarderingen":"56","scoreGemiddeld":6.9,"zorgaanbiederUrl":"https://www.zorgkaartnederland.nl/zorginstelling/ziekenhuis-diakonessenhuis-locatie-utrecht-utrecht-111221","opmerking":null,"zorgKaartNLId":"111221","waardeerURL":"https://www.zorgkaartnederland.nl/zorginstelling/ziekenhuis-diako
```

### GET 200 https://api.vgz.nl/zorgzoeker/api/v2/zorgaanbieder/autocomplete/vgz/2027/'Ziekenhuis'?maxaantal=5 (3,458 tekens)

```
{"totaalAantalResultaten":308,"zoekresultaat":[{"zorgaanbiederId":819899,"zorgaanbiederUniekId":"532164719754-brocacef-ziekenhuisfarmacie","indAdresOpenbaar":true,"agbCode":"71171988","agbCodeOnderneming":"02009992","naam":"BROCACEF ZIEKENHUISFARMACIE","straat":"De Amfoor","huisnummer":"1","huisnummerToevoeging":null,"postcode":"5807GW","plaatsnaam":"OOSTRUM LB","landCode":"NL","locatie":{"lengtegraad":6.00490813,"breedtegraad":51.52261213},"afstand":null,"zorgsoortCodes":["016","PALKIT"],"displayNaam":"BROCACEF <b>ZIEKENHUIS</b>FARMACIE, OOSTRUM LB","searchScore":20},{"zorgaanbiederId":823565,"zorgaanbiederUniekId":"974054499909-brocacef-ziekenhuisfarmacie-den-haag","indAdresOpenbaar":true,"agbCode":"71193800","agbCodeOnderneming":"02010948","naam":"BROCACEF ZIEKENHUISFARMACIE DEN HAAG","straat":"Charlotte Jacobslaan","huisnummer":"70","huisnummerToevoeging":null,"postcode":"2545AB","plaatsnaam":"'S-GRAVENHAGE","landCode":"NL","locatie":{"lengtegraad":4.2623684,"breedtegraad":52.05548871},"afstand":null,"zorgsoortCodes":["016","PALKIT"],"displayNaam":"BROCACEF <b>ZIEKENHUIS</b>FARMACIE DEN HAAG, 'S-GRAVENHAGE","searchScore":20},{"zorgaanbiederId":792140,"zorgaanbiederUniekId":"310138599647-sionsberg-netwerk-ziekenhuis","indAdresOpenbaar":true,"agbCode":"22220769","agbCodeOnderneming":"22220769","naam":"Sionsberg Netwerk Ziekenhuis","straat":"Birdaarderstraatweg","huisnummer":"70","huisnummerToevoeging":null,"postcode":"9101DC","plaatsnaam":"DOKKUM","landCode":"NL","locatie":{"lengtegraad":5.99177822,"breedtegraad":53.32035612},"afstand":null,"zorgsoortCodes":["000900","001700","002400","003100","003200","003800","004500","007800","008200","008300","009200","009600","009900","010500","010900","011600","014200","015","015.0200","015.0300","015.0500","015.0600","015.0700","015.1000","015.1100","015.1200","015.1400","015.1700","015.1800","015.2000","015.2300","015.2500","015200","016500","017200","018000","019300","021000","023900","024600","024800","027100","028500","030500","031200","032200","032400","033400","033800","033900","035400","036300","036400","036500","036800","043800","044200","044300","045400","050100","050200","050400","051200","051700","052600","058400","058900","062600"],"displayNaam":"Sionsberg Netwerk <b>Ziekenhuis</b>, DOKKUM","searchScore":20},{"zorgaanbiederId":791787,"zorgaanbiederUniekId":"293638586284-vitalys-loc-ziekenhuis-gelderse-vallei","indAdresOpenbaar":true,"agbCode":"22220091","agbCodeOnderneming":"22220091","naam":"Vitalys, loc. Ziekenhuis Gelderse Vallei","straat":"Willy Brandtlaan","huisnummer":"10","huisnummerToevoeging":null,"postcode":"6716RP","plaatsnaam":"EDE","landCode":"NL","locatie":{"lengtegraad":5.64556294,"breedtegraad":52.02244298},"afstand":null,"zorgsoortCodes":["015","015.0600","015.0700","025700","028900"],"displayNaam":"Vitalys, loc. <b>Ziekenhuis</b> Gelderse Vallei, EDE","searchScore":20},{"zorgaanbiederId":809260,"zorgaanbiederUniekId":"355986105455-canisiuswilhelmina-ziekenhuis-paaz","indAdre
```

### GET 200 https://api.vgz.nl/clf-service-gebruikersmenu/api/gebruikersmenu?ingelogd=false&x_client=vgz-iml&x_language=nl-NL (1,327 tekens)

```
{"data":{"gebruikersMenuItems":[{"titel":"Mijn zorgverzekering","link":"https://app.vgz.nl/link/polis?utm_campaign=fn_website-menu-inloggen&amp;utm_medium=web&amp;utm_source=oo","showAsButton":false},{"titel":"Mijn declaratieoverzicht","link":"https://app.vgz.nl/link/verbruikte-zorg?utm_campaign=fn_website-menu-inloggen&amp;utm_medium=web&amp;utm_source=oo","showAsButton":false},{"titel":"Mijn vergoedingen","link":"https://mijn.vgz.nl/vergoedingen","showAsButton":false},{"titel":"Mijn eigen risico","link":"https://app.vgz.nl/link/eigen-risico?utm_campaign=fn_website-menu-inloggen&amp;utm_medium=web&amp;utm_source=oo","showAsButton":false},{"titel":"Mijn facturen","link":"https://app.vgz.nl/link/facturen?utm_campaign=fn_website-menu-inloggen&amp;utm_medium=web&amp;utm_source=oo","showAsButton":false},{"titel":"Mijn postvak","link":"https://app.vgz.nl/link/postvak?utm_campaign=fn_website-menu-inloggen&amp;utm_medium=web&amp;utm_source=oo","showAsButton":false},{"titel":"Mijn gegevens","link":"https://mijn.vgz.nl/gegevens/wijzigen","showAsButton":false},{"titel":"Declaratie indienen","link":"https://app.vgz.nl/link/voor-wie-wilt-u-declareren?utm_campaign=fn_website-menu-inloggen&amp;utm_medium=web&amp;utm_source=oo","showAsButton":false},{"titel":"Inloggen","link":"https://mijn.vgz.nl","showAsButton":true}]}}
```

### GET 200 https://api.vgz.nl/zorgzoeker/api/v2/zorgsoort/autocomplete/vgz/2027/'Ziekenhuis'?maxaantal=5 (1,263 tekens)

```
[{"uniqueId":"2027_185658_6","uri":"http://uvit.nl/CS/Zorgsoort/V1/015","code":"015","zorgsoortType":null,"naam":"Ziekenhuizen en klinieken","synoniem":"Ziekenhuis","niveau":1,"standaardZoekRadius":50,"heeftVerzorgingsgebied":false,"heeftZorgaanbieders":true,"parentNaam":null,"parentUri":null,"displayNaam":"<b>Ziekenhuis</b> (Ziekenhuizen en klinieken)","searchScore":3.4353158},{"uniqueId":"2027_185938_0","uri":"http://uvit.nl/CS/Zorgsoort/V1/015.2000","code":"015.2000","zorgsoortType":null,"naam":"Ziekenhuis onderzoek","synoniem":null,"niveau":2,"standaardZoekRadius":50,"heeftVerzorgingsgebied":false,"heeftZorgaanbieders":true,"parentNaam":"Ziekenhuizen en klinieken","parentUri":"http://uvit.nl/CS/Zorgsoort/V1/015","displayNaam":"<b>Ziekenhuis</b> onderzoek","searchScore":2.093168},{"uniqueId":"2027_185938_3","uri":"http://uvit.nl/CS/Zorgsoort/V1/015.2000","code":"015.2000","zorgsoortType":null,"naam":"Ziekenhuis onderzoek","synoniem":"onderzoek in het ziekenhuis","niveau":2,"standaardZoekRadius":50,"heeftVerzorgingsgebied":false,"heeftZorgaanbieders":true,"parentNaam":"Ziekenhuizen en klinieken","parentUri":"http://uvit.nl/CS/Zorgsoort/V1/015","displayNaam":"onderzoek in het <b>ziekenhuis</b> (Ziekenhuis onderzoek)","searchScore":1.6012607}]
```

### GET 200 https://api.vgz.nl/zorgzoeker/api/v2/zorgsoort/vgz/2027/015?uniqueId=2027_185658_6 (465 tekens)

```
{"naam":"Ziekenhuis","omschrijving":null,"uri":"http://uvit.nl/CS/Zorgsoort/V1/015","uniqueId":"2027_185658_6","code":"015","parentNaam":null,"parentUri":null,"parentCode":null,"zorgsoortType":"careType","synoniemVan":"Ziekenhuizen en klinieken","niveau":1,"standaardZoekRadius":50,"heeftVerzorgingsgebied":false,"heeftResultaten":true,"heeftZorgaanbieders":true,"toonMedewerkers":false,"toonContractFilter":true,"zoekresultaatTekstKort":"","zoekresultaatTekst":""}
```

### GET 200 https://vb-pr-am.vgz.nl/chat-api/settings?settingNames=UseFormalStyle&settingNames=BotName&brandCode=VGZ (432 tekens)

```
[
  {
    "name": "UseFormalStyle",
    "value": "False",
    "dataType": "System.Boolean",
    "brand": {
      "id": 2,
      "code": "VGZ",
      "name": "VGZ",
      "isEnabled": false,
      "settings": []
    }
  },
  {
    "name": "BotName",
    "value": "Sam",
    "dataType": "System.String",
    "brand": {
      "id": 2,
      "code": "VGZ",
      "name": "VGZ",
      "isEnabled": false,
      "settings": []
    }
  }
]
```

### POST 200 https://dc.services.visualstudio.com/v2/track (98 tekens)

Verzonden:
```
[{"time":"2026-11-25T20:48:24.169Z","iKey":"3e19b529-e9ba-4d81-b93f-beb91c0082f4","name":"Microsoft.ApplicationInsights.3e19b529e9ba4d81b93fbeb91c0082f4.RemoteDependency","tags":{"ai.user.id":"jK59mT9Ni3Q/MhTl5DVDQg","ai.session.id":"dBngCteU2SnUiu6WjAQnoU","ai.device.id":"browser","ai.device.type":"Browser","ai.operation.name":"/zorg-regelen/zorgzoeker","ai.operation.id":"ccd780cbd83645d3912b19670b97e27f","ai.internal.sdkVersion":"javascript:2.8.18","ai.cloud.role":"zorgzoeker"},"data":{"baseType":"RemoteDependencyData","baseData":{"id":"|ccd780cbd83645d3912b19670b97e27f.071945fef92f4b29.","ver":2,"name":"GET https://maps.googleapis.com/maps/api/mapsjs/gen_204?csp_test=true","resultCode":"200","duration":"00:00:00.034","success":true,"data":"GET https://maps.googleapis.com/maps/api/mapsjs/gen_204?csp_test=true","target":"maps.googleapis.com","type":"Ajax","properties":{"HttpMethod":"GET","ApplicationId":"zorgzoeker","ProgramId":"OO","MerkCode":"VGZ","Environment":"P","BuildNumber":"20261104-2"},"measurements":{}}}},{"time":"2026-11-25T20:48:24.068Z","iKey":"3e19b529-e9ba-4d81-b93f-beb91c0082f4","name":"Microsoft.ApplicationInsights.3e19b529e9ba4d81b93fbeb91c0082f4.RemoteDependency","tags":{"ai.user.id":"jK59mT9Ni3Q/MhTl5DVDQg","ai.session.id":"dBngCteU2SnUiu6WjAQnoU","ai.device.id":"browser","ai.device.type":"Browser","ai.operation.name":"/zorg-regelen/zorgzoeker","ai.operation.id":"ccd780cbd83645d3912b19670b97e27f","ai.internal.sdkVersion":"javascript:2.8.18","ai.cloud.role
```
```
{"itemsReceived":13,"itemsAccepted":13,"appId":"4c09065e-fbc0-411d-942e-798bce811f99","errors":[]}
```

### POST 200 https://dc.services.visualstudio.com/v2/track (98 tekens)

Verzonden:
```
[{"time":"2026-11-25T20:48:43.488Z","iKey":"3e19b529-e9ba-4d81-b93f-beb91c0082f4","name":"Microsoft.ApplicationInsights.3e19b529e9ba4d81b93fbeb91c0082f4.RemoteDependency","tags":{"ai.user.id":"jK59mT9Ni3Q/MhTl5DVDQg","ai.session.id":"dBngCteU2SnUiu6WjAQnoU","ai.device.id":"browser","ai.device.type":"Browser","ai.operation.name":"/zorg-regelen/zorgzoeker/zoekresultaten","ai.operation.id":"68823b91b5f14375a24bd301ed34eb6b","ai.internal.sdkVersion":"javascript:2.8.18","ai.cloud.role":"zorgzoeker"},"data":{"baseType":"RemoteDependencyData","baseData":{"id":"|68823b91b5f14375a24bd301ed34eb6b.910df80b565c4ff1.","ver":2,"name":"GET https://api.vgz.nl/zorgzoeker/api/v2/resource/vgz","resultCode":"200","duration":"00:00:00.443","success":true,"data":"GET https://api.vgz.nl/zorgzoeker/api/v2/resource/vgz","target":"api.vgz.nl","type":"Ajax","properties":{"HttpMethod":"GET","ApplicationId":"zorgzoeker","ProgramId":"OO","MerkCode":"VGZ","Environment":"P","BuildNumber":"20261104-2"},"measurements":{}}}},{"time":"2026-11-25T20:48:43.964Z","iKey":"3e19b529-e9ba-4d81-b93f-beb91c0082f4","name":"Microsoft.ApplicationInsights.3e19b529e9ba4d81b93fbeb91c0082f4.Event","tags":{"ai.user.id":"jK59mT9Ni3Q/MhTl5DVDQg","ai.session.id":"dBngCteU2SnUiu6WjAQnoU","ai.device.id":"browser","ai.device.type":"Browser","ai.operation.name":"/zorg-regelen/zorgzoeker/zoekresultaten","ai.operation.id":"68823b91b5f14375a24bd301ed34eb6b","ai.internal.sdkVersion":"javascript:2.8.18","ai.cloud.role":"zorgzoeker"},"data"
```
```
{"itemsReceived":95,"itemsAccepted":95,"appId":"4c09065e-fbc0-411d-942e-798bce811f99","errors":[]}
```

### POST 200 https://dc.services.visualstudio.com/v2/track (96 tekens)

Verzonden:
```
[{"time":"2026-11-25T20:48:21.917Z","iKey":"1a60808c-e79e-4613-8e2d-a1dc5da2812e","name":"Microsoft.ApplicationInsights.1a60808ce79e46138e2da1dc5da2812e.Message","tags":{"ai.user.id":"jK59mT9Ni3Q/MhTl5DVDQg","ai.session.id":"dBngCteU2SnUiu6WjAQnoU","ai.device.id":"browser","ai.device.type":"Browser","ai.operation.name":"/zorg-regelen/zorgzoeker","ai.operation.id":"5595026659604088be55892d14074776","ai.internal.sdkVersion":"javascript:3.4.1","ai.internal.snippet":"-"},"data":{"baseType":"MessageData","baseData":{"ver":2,"message":"Utils.Log - undefined *** ChatbotComponent: init","severityLevel":1,"properties":{"params":"[{\"appInsights\":{\"enabled\":true,\"instrumentationKey\":\"1a60808c-e79e-4613-8e2d-a1dc5da2812e\"},\"autoStart\":false,\"brandLabel\":\"VGZ\",\"chatApiStatusUrl\":\"https://vb-pr-am.vgz.nl/chat-api/status\",\"chatApiUrl\":\"https://vb-pr-am.vgz.nl/chat-api/\",\"chatButtonHidden\":false,\"embedded\":false,\"environmentString\":\"OO\",\"showOffline\":false,\"signalRApiPostfix\":\"signalr\"}]","MerkCode":"VGZ"}}}}]
```
```
{"itemsReceived":1,"itemsAccepted":1,"appId":"4f0376cb-a1ad-461a-a675-ff518fd67457","errors":[]}
```

### POST 200 https://dc.services.visualstudio.com/v2/track (96 tekens)

Verzonden:
```
[{"time":"2026-11-25T20:48:21.917Z","iKey":"1a60808c-e79e-4613-8e2d-a1dc5da2812e","name":"Microsoft.ApplicationInsights.1a60808ce79e46138e2da1dc5da2812e.Message","tags":{"ai.user.id":"jK59mT9Ni3Q/MhTl5DVDQg","ai.session.id":"dBngCteU2SnUiu6WjAQnoU","ai.device.id":"browser","ai.device.type":"Browser","ai.operation.name":"/zorg-regelen/zorgzoeker","ai.operation.id":"5595026659604088be55892d14074776","ai.internal.sdkVersion":"javascript:3.4.1","ai.internal.snippet":"-"},"data":{"baseType":"MessageData","baseData":{"ver":2,"message":"Utils.Log - undefined *** ChatbotComponent: init","severityLevel":1,"properties":{"params":"[{\"appInsights\":{\"enabled\":true,\"instrumentationKey\":\"1a60808c-e79e-4613-8e2d-a1dc5da2812e\"},\"autoStart\":false,\"brandLabel\":\"VGZ\",\"chatApiStatusUrl\":\"https://vb-pr-am.vgz.nl/chat-api/status\",\"chatApiUrl\":\"https://vb-pr-am.vgz.nl/chat-api/\",\"chatButtonHidden\":false,\"embedded\":false,\"environmentString\":\"OO\",\"showOffline\":false,\"signalRApiPostfix\":\"signalr\"}]","MerkCode":"VGZ"}}}},{"time":"2026-11-25T20:48:22.395Z","iKey":"1a60808c-e79e-4613-8e2d-a1dc5da2812e","name":"Microsoft.ApplicationInsights.1a60808ce79e46138e2da1dc5da2812e.Message","tags":{"ai.user.id":"jK59mT9Ni3Q/MhTl5DVDQg","ai.session.id":"dBngCteU2SnUiu6WjAQnoU","ai.device.id":"browser","ai.device.type":"Browser","ai.operation.name":"/zorg-regelen/zorgzoeker","ai.operation.id":"b1270574b25448788f56188defcf22e6","ai.internal.sdkVersion":"javascript:3.4.1","ai.interna
```
```
{"itemsReceived":3,"itemsAccepted":3,"appId":"4f0376cb-a1ad-461a-a675-ff518fd67457","errors":[]}
```

### GET 200 https://geolocation.onetrust.com/cookieconsentpub/v1/geo/location (69 tekens)

```
{"country":"US","state":"VA","stateName":"Virginia","continent":"NA"}
```

### GET 200 https://api.vgz.nl/zorgzoeker/api/v2/verwerkingsdatum/vgz (51 tekens)

```
{"verwerkingsdatum":"2026-11-24T20:28:02.15+00:00"}
```

### GET 200 https://api.vgz.nl/zorgzoeker/api/v2/zorgsoort/015/landcodes (6 tekens)

```
["NL"]
```

### GET 200 https://api.vgz.nl/zorgzoeker/api/v2/zorgsoort/015/landcodes (6 tekens)

```
["NL"]
```

### GET 200 https://api.vgz.nl/sgw/auth/user?slide=false&x_client=vgz-iml (4 tekens)

```
null
```

### GET 200 https://vb-pr-am.vgz.nl/chat-api/status/chat-enabled?brandCode=VGZ&environment=OO (4 tekens)

```
true
```

### GET 200 https://maps.googleapis.com/maps/api/mapsjs/gen_204?csp_test=true (3 tekens)

```
{}

```

### GET 200 https://api.vgz.nl/zorgzoeker/api/v2/polistype/vgz/2027 (2 tekens)

```
[]
```

### POST 200 https://dc.services.visualstudio.com/v2/track (0 tekens)

```

```

