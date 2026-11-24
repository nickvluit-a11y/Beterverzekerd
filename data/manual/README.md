# Handmatige referentiedata

Deze bestanden worden met de hand bijgehouden (of na controle overgenomen uit `data/processed/`).
De kolom `verified` staat op `false` zolang een waarde niet tegen een primaire bron is gecontroleerd.

| Bestand | Inhoud | Hoe bijwerken |
|---|---|---|
| `hospitals.csv` | Ziekenhuislocaties: id, organisatie, AGB-code, adres, coördinaten, aliassen (gescheiden door `\|`), URL van het contractoverzicht | Nieuwe locatie = nieuwe regel. Aliassen toevoegen als een bron een andere naam gebruikt (de pipeline laat onbekende namen zien). |
| `concerns_labels.csv` | Welk label bij welk concern hoort | Elk najaar controleren (labels komen en gaan, bv. ONVZ → VGZ in 2027). |
| `procedures.csv` | De ingrepen en zoekpatronen (regex) voor Zorginzicht en NZa | Patroon aanpassen als de echte indicatornamen anders blijken (zie `docs/data_inventory/`). |
| `contracts.csv` | **Gecontroleerde** contractstatus per locatie × concern/label × jaar | Overnemen uit `data/processed/contracts_candidates.csv` nadat je ze naast de bron-PDF hebt gelegd. `label` leeg = geldt voor het hele concern. `status`: `gecontracteerd`, `in_onderhandeling`, `geen_contract`, `onbekend`. `omzetplafond`: `true`/`false`/leeg. Oude regels laten staan (historie). |
| `polissen_2027.csv` | Polissen met type (`natura`/`restitutie`/`combinatie`/`budget`), premie en vergoeding bij niet-gecontracteerde zorg | Overnemen van zorgverzekeringskaart.nl. Zolang dit leeg is, toont de app één regel per label. |

Waarom handmatig? Voor ~12 ziekenhuizen en ~60 polissen is overtikken sneller en betrouwbaarder dan een scraper
per website. Automatiseren pas als de lijst groeit.
