# Zorgzoeker menzis (browser-verkenning 2026-11-25)

- start: https://www.menzis.nl/zorg-en-vergoedingen/de-zorgvinder
- link 'Naar de Zorgvinder': /zorgvinder
- zoekpagina: https://zorgvinder.menzis.nl/

## Invoervelden

- autocomplete__search Bijvoorbeeld: Fysiotherapie of Ziekenhuis Welke zorg of zorgaanbieder zoek je? Welke zorg of zorgaanbieder zoek je? (INPUT/text)
- autocomplete__location Postcode of woonplaats Waar zoek je deze zorg? Waar zoek je deze zorg? (INPUT/text)
- range  Selecteer een afstand. Maximale afstand (SELECT/select-one)
- #autocomplete__search: gekozen suggestie voor Ziekenhuis
- #autocomplete__location: gekozen suggestie voor 3584 CX

- na zoeken: https://zorgvinder.menzis.nl/
- zichtbare tekst: 1,737 tekens
- JSON-antwoorden voor/na zoeken: 7/2

## JSON-antwoorden na het zoeken (grootste eerst)

Volledige data van de grootste aanroep: finder_browser_menzis.json

### GET 200 https://zorgvinder.menzis.nl/api/zadvies/MENZIS_ZZ/zorginkoop/zoektermenPerType?zoekterm=Ziekenhuis&zoektermTypes=TYPE_ZORGAANBIEDER,SPECIALISME,AANDOENING,BEHANDELING,VESTIGING,ZORGAANBIEDER,VRIJE_ZOEKTERM&aantal=14 (6,594 tekens)

```
{
  "TYPE_ZORGAANBIEDER" : [ ],
  "SPECIALISME" : [ {
    "id" : "1140736692",
    "weergaveWaarde" : "Ziekenhuis / ZBC",
    "zoekWaarde" : "ziekenhuis / zbc",
    "zoektermType" : "SPECIALISME",
    "referentieId" : "220906197"
  } ],
  "AANDOENING" : [ ],
  "BEHANDELING" : [ ],
  "VESTIGING" : [ {
    "id" : "1140736673",
    "weergaveWaarde" : "Ziekenhuisgroep Twente (Psychiatrie) (Vestiging)",
    "zoekWaarde" : "ziekenhuisgroep twente (psychiatrie)",
    "zoektermType" : "VESTIGING",
    "referentieId" : "51159679"
  }, {
    "id" : "1140736682",
    "weergaveWaarde" : "Ziekenhuis Nij Smellinghe, loc. Dokkum (Vestiging)",
    "zoekWaarde" : "ziekenhuis nij smellinghe, loc. dokkum",
    "zoektermType" : "VESTIGING",
    "referentieId" : "214346381"
  }, {
    "id" : "1140736669",
    "weergaveWaarde" : "Ziekenhuis Gelderse Vallei (ZGV) (Vestiging)",
    "zoekWaarde" : "ziekenhuis gelderse vallei (zgv)",
    "zoektermType" : "VESTIGING",
    "referentieId" : "51226417"
  }, {
    "id" : "1140736672",
    "weergaveWaarde" : "Ziekenhuis Gelderse Vallei (ZGV), polikliniek Wageningen (Vestiging)",
    "zoekWaarde" : "ziekenhuis gelderse vallei (zgv), polikliniek wageningen",
    "zoektermType" : "VESTIGING",
    "referentieId" : "215437063"
  }, {
    "id" : "1140736678",
    "weergaveWaarde" : "Ziekenhuis Groep Twente (ZGT), loc. buitenpolikliniek Rijssen (Vestiging)",
    "zoekWaarde" : "ziekenhuis groep twente (zgt), loc. buitenpolikliniek rijssen",
    "zoektermType" : "VESTIGING",
    "referentieId" : "51225952"
  }, {
    "id" : "1140736680",
    "weergaveWaarde" : "Ziekenhuis Nij Smellinghe (Vestiging)",
    "zoekWaarde" : "ziekenhuis nij smellinghe",
    "zoektermType" : "VESTIGING",
    "referentieId" : "51225903"
  }, {
    "id" : "1140736664",
    "weergaveWaarde" : "Ziekenhuis Amstelland (Vestiging)",
    "zoekWaarde" : "ziekenhuis amstelland",
    "zoektermType" : "VESTIGING",
    "referentieId" : "51123060"
  }, {
    "id" : "1140736665",
    "weergaveWaarde" : "Ziekenhuis Amstelland, loc. Gezondheidscentrum de Waterlinie (Vestiging)",
    "zoekWaarde" : "ziekenhuis amstelland, loc. gezondheidscentrum de waterlinie",
    "zoektermType" : "VESTIGING",
    "referentieId" : "51227051"
  }, {
    "id" : "1140736670",
    "weergaveWaarde" : "Ziekenhuis Gelderse Vallei (ZGV), loc. Barneveld (Vestiging)",
    "zoekWaarde" : "ziekenhuis gelderse vallei (zgv), loc. barneveld",
    "zoektermType" : "VESTIGING",
    "referentieId" : "215437364"
  }, {
    "id" : "1140736671",
    "weergaveWaarde" : "Ziekenhuis Gelderse Vallei (ZGV), loc. polikliniek Veenendaal (Vestiging)",
    "zoekWaarde" : "ziekenhuis gelderse vallei (zgv), loc. polikliniek veenendaal",
    "zoektermType" : "VESTIGING",
    "referentieId" : "215436846"
  }, {
    "id" : "1140736676",
    "weergaveWaarde" : "Ziekenhuis Groep Twente (ZGT), loc. Almelo (Vestiging)",
    "zoekWaarde" : "ziekenhuis groep twente (zgt), loc. almelo",
    "zoektermType" : "VESTIGING",
    "referent
```

### GET 200 https://zorgvinder.menzis.nl/api/zadvies/MENZIS_ZZ/zorginkoop/postcode?zoekterm=3584%20CX (86 tekens)

```
[ {
  "postcode" : "3584CX",
  "straat" : "Heidelberglaan",
  "plaats" : "Utrecht"
} ]
```

