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

- na zoeken: https://zorgvinder.menzis.nl/?search=zorgaanbieder&zoektermSearch=ziekenhuis%20%2F%20zbc&zoektermType=SPECIALISME&specialismId=220906197&afstand=35&postcode=3584CX
- zichtbare tekst: 3,803 tekens
- JSON-antwoorden voor/na zoeken: 7/6

## JSON-antwoorden na het zoeken (grootste eerst)

### POST 200 https://zorgvinder.menzis.nl/api/zadvies/MENZIS_ZZ/zorginkoop/zorgaanbieders (203,810 tekens)

Verzonden:
```
{"zorgaanbieder":{"type":""},"locatiebepaling":{"afstandKm":35,"postcode":"3584CX"},"paginaEnSortering":{"offset":0,"aantal":10,"sortering":"afstand"},"pakketIds":["H231538222"],"pakketLijst":"voor_advies_2027","zoektermId":"1140736692","specialismeIds":["220906197"],"aannameNieuwePatienten":false}
```
```
{
  "aantal" : 194,
  "zorgaanbieders" : [ {
    "id" : "51228215",
    "naam" : "UMC Utrecht (UMC Utrecht, loc. AZU)",
    "type" : "ZIEKENHUIS",
    "agbCode" : "06020602",
    "naamZorgaanbieder" : "UMC Utrecht",
    "naamVestiging" : "UMC Utrecht, loc. AZU",
    "straat" : "Heidelberglaan",
    "huisnummer" : "100",
    "postcode" : "3584CX",
    "plaats" : "Utrecht",
    "land" : "NL",
    "email" : "info@umcutrecht.nl",
    "website" : "www.umcutrecht.nl",
    "telefoonnummer" : "0887555555",
    "latitude" : 52.086020488463085,
    "longitude" : 5.179601778635905,
    "afstand" : 0.1,
    "landelijkeDekking" : false,
    "specialismen" : [ {
      "id" : "51277359",
      "naam" : "Allergologie",
      "aandoeningen" : [ {
        "id" : "221080483",
        "naam" : "Allergie - Allergologie"
      }, {
        "id" : "59526898",
        "naam" : "Hooikoorts"
      }, {
        "id" : "59527161",
        "naam" : "Voedselallergie"
      } ]
    }, {
      "id" : "51277371",
      "naam" : "Anaesthesiologie",
      "aandoeningen" : [ {
        "id" : "59527044",
        "naam" : "Pijnbestrijding"
      }, {
        "id" : "220883364",
        "naam" : "Pijnrevalidatie - Pijnbestrijding"
      }, {
        "id" : "221080482",
        "naam" : "Ruggenmergstimulatie - Anesthesie"
      }, {
        "id" : "221298815",
        "naam" : "Rugklachten - Pijnbestrijding"
      }, {
        "id" : "59527086",
        "naam" : "Rugpijn na een operatie"
      }, {
        "id" : "147941127",
        "naam" : "Verdoving bij operatie"
      } ]
    }, {
      "id" : "51277356",
      "naam" : "Cardiologie",
      "aandoeningen" : [ {
        "id" : "220917721",
        "naam" : "Aangeboren hartafwijkingen"
      }, {
        "id" : "59526659",
        "naam" : "Aderverkalking"
      }, {
        "id" : "59526675",
        "naam" : "Angina pectoris"
      }, {
        "id" : "220883358",
        "naam" : "Cardiologische revalidatie - Cardiologie"
      }, {
        "id" : "221002628",
        "naam" : "Carotisstenose - Cardiologie"
      }, {
        "id" : "221202127",
        "naam" : "Coronaire microvasculaire dysfunctie"
      }, {
        "id" : "59526794",
        "naam" : "Dotteren"
      }, {
        "id" : "220903221",
        "naam" : "Elektrocardiogram"
      }, {
        "id" : "220883374",
        "naam" : "Elektrofysiologisch Onderzoek (EFO)"
      }, {
        "id" : "59526812",
        "naam" : "Embolie"
      }, {
        "id" : "221202121",
        "naam" : "Hart ablatie"
      }, {
        "id" : "59526873",
        "naam" : "Hartfalen"
      }, {
        "id" : "59526874",
        "naam" : "Hartgeruis"
      }, {
        "id" : "59526875",
        "naam" : "Hartinfarct"
      }, {
        "id" : "221140417",
        "naam" : "Hartkatheterisatie"
      }, {
        "id" : "59526876",
        "naam" : "Hartklepafwijking"
      }, {
        "id" : "90464901",
        "naam" : "Hartklepinterventie"
      }, {
        "id" : "59526878",
  
```

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

### POST 200 https://zorgvinder.menzis.nl/cms/search-page-content/search/menzis?draft=false&label=menzis&limit=0 (4,030 tekens)

Verzonden:
```
{"zorgaanbiederType":"ZIEKENHUIS","specialismen":["220906197"]}
```
```
[{"id":69,"contentPerYear":[{"id":"6a2ac21015510bd0e4d02474","year":"all","contentblocks":[{"id":"6a2ac21015510bd0e4d02473","title":"Toelichting","body":{"root":{"type":"root","format":"","indent":0,"version":1,"children":[{"tag":"h3","type":"heading","format":"","indent":0,"version":1,"children":[{"mode":"normal","text":"Contracteerstatussen","type":"text","style":"","detail":0,"format":0,"version":1}],"direction":null},{"type":"paragraph","format":"","indent":0,"version":1,"children":[{"mode":"normal","text":"Onderstaande statussen zie je terug in de zorgvinder. Meer informatie over wat de status voor jouw vergoeding betekent, lees je onder 'bekijk details' per zorgaanbieder. Deze toelichting gaat over de naturapolis of (bij een combinatiepolis) over het natura-deel van je zorgverzekering. In je verzekeringsvoorwaarden lees je welke polis je hebt.","type":"text","style":"","detail":0,"format":0,"version":1}],"direction":null,"textStyle":"","textFormat":0},{"tag":"ul","type":"list","start":1,"format":"","indent":0,"version":1,"children":[{"type":"listitem","value":1,"format":"","indent":0,"version":1,"children":[{"mode":"normal","text":"Contract: vergoed","type":"text","style":"","detail":0,"format":0,"version":1}],"direction":null},{"type":"listitem","value":2,"format":"","indent":0,"version":1,"children":[{"mode":"normal","text":"(Nog) geen contract: wel vergoed","type":"text","style":"","detail":0,"format":0,"version":1}],"direction":null},{"type":"listitem","value":3,"format":"","indent":0,"version":1,"children":[{"mode":"normal","text":"Nog geen contract: een deel niet vergoed","type":"text","style":"","detail":0,"format":0,"version":1}],"direction":null},{"type":"listitem","value":4,"format":"","indent":0,"version":1,"children":[{"mode":"normal","text":"Geen contract: een deel niet vergoed","type":"text","style":"","detail":0,"format":0,"version":1}],"direction":null}],"listType":"bullet","direction":null},{"tag":"h3","type":"heading","format":"","indent":0,"version":1,"children":[{"mode":"normal","text":"Maximumbedrag of omzetplafond","type":"text","style":"","detail":0,"format":0,"version":1}],"direction":null},{"type":"paragraph","format":"","indent":0,"version":1,"children":[{"mode":"normal","text":"Met een aantal zorgaanbieders maken wij afspraken over hoeveel zorg zij per jaar bij ons in rekening mogen brengen. Dat noemen we maximumbedrag of omzetplafond. Heeft je zorgaanbieder de maximale hoeveelheid zorg bereikt voor dat jaar? Dan kun je voor een nieuwe behandeling misschien niet meer naar deze zorgaanbieder. Onze Zorgadviseur helpt je dan graag bij het vinden van een zorgaanbieder bij jou in de buurt. Je leest bij 'Bekijk details' of we met jouw zorgaanbieder een maximumbedrag hebben afgesproken.","type":"text","style":"","detail":0,"format":0,"version":1}],"direction":null,"textStyle":"","textFormat":0}],"direction":null}},"position":"primary","color":"primary","startDate":null,"endDate":null,"blockName":null,"blockType":"content
```

### POST 200 https://zorgvinder.menzis.nl/api/zadvies/MENZIS_ZZ/zorginkoop/zorgaanbieders/filters (659 tekens)

Verzonden:
```
{"zoektermId":"1140736692","locatiebepaling":{"afstandKm":35,"postcode":"3584CX"}}
```
```
{
  "zoekterm" : {
    "id" : "1140736692",
    "weergaveWaarde" : "Ziekenhuis / ZBC",
    "zoekWaarde" : "ziekenhuis / zbc",
    "zoektermType" : "SPECIALISME",
    "referentieId" : "220906197"
  },
  "locatie" : {
    "postcode" : "3584CX",
    "afstandKm" : 35
  },
  "aantalResultatenZonderFilters" : 194,
  "contractStatussen" : [ "GECONTRACTEERD", "GEEN_CONTRACT_WEL_VERGOED", "GEEN_CONTRACT_VERGOED_TIJDENS_ONDERHANDELING", "IN_ONDERHANDELING", "NIET_GECONTRACTEERD", "ONBEKEND", "ONBEPAALD" ],
  "specialismen" : [ {
    "id" : "220906197",
    "specialismeExternId" : "220906197",
    "naam" : "Ziekenhuis / ZBC"
  } ],
  "zorgaanbiederTypes" : [ ]
}
```

### GET 200 https://zorgvinder.menzis.nl/api/zadvies/MENZIS_ZZ/zorginkoop/postcode?zoekterm=3584%20CX (86 tekens)

```
[ {
  "postcode" : "3584CX",
  "straat" : "Heidelberglaan",
  "plaats" : "Utrecht"
} ]
```

### GET 200 https://zorgvinder.menzis.nl/api/zadvies/MENZIS_ZZ/zorginkoop/postcode/3584CX (82 tekens)

```
{
  "postcode" : "3584CX",
  "straat" : "Heidelberglaan",
  "plaats" : "Utrecht"
}
```

