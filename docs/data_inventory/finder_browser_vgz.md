# Zorgzoeker vgz (browser-verkenning 2026-11-25)

- start: https://www.vgz.nl/zorg-regelen/zorgzoeker
- zoekpagina: https://www.vgz.nl/zorg-regelen/zorgzoeker#/filter

## Invoervelden

- search Ik ben op zoek naar... (INPUT/search)
- zoekterm zoekterm Welke zorg(verlener) zoek je?  Welke zorg(verlener) zoek je? (INPUT/text)
- locatie locatie Wat is je postcode of plaats?  In welke omgeving zoekt u? (INPUT/text)
- afstand afstand   afstand (SELECT/select-one)
- vendor-search-handler vendor-search-handler Zoeken… Zoeken in cookielijsten (INPUT/text)
- invullen Ziekenhuis: TimeoutError
- zoeken: TimeoutError

- na zoeken: https://www.vgz.nl/zorg-regelen/zorgzoeker#/filter
- zichtbare tekst: 2,943 tekens
- JSON-antwoorden voor/na zoeken: 17/3

## JSON-antwoorden na het zoeken (grootste eerst)

### POST 200 https://dc.services.visualstudio.com/v2/track (98 tekens)

Verzonden:
```
[{"time":"2026-11-25T13:38:46.357Z","iKey":"3e19b529-e9ba-4d81-b93f-beb91c0082f4","name":"Microsoft.ApplicationInsights.3e19b529e9ba4d81b93fbeb91c0082f4.RemoteDependency","tags":{"ai.user.id":"rBvKb1AELFhw2eMIpNKhqF","ai.session.id":"48sPaUnMsgKBa2CdjKTb2O","ai.device.id":"browser","ai.device.type":"Browser","ai.operation.name":"/zorg-regelen/zorgzoeker","ai.operation.id":"3b9d1a2ac1c94a619a6651147ae818b7","ai.internal.sdkVersion":"javascript:2.8.18","ai.cloud.role":"zorgzoeker"},"data":{"baseTy
```
```
{"itemsReceived":11,"itemsAccepted":11,"appId":"4c09065e-fbc0-411d-942e-798bce811f99","errors":[]}
```

### POST 200 https://dc.services.visualstudio.com/v2/track (96 tekens)

Verzonden:
```
[{"time":"2026-11-25T13:38:44.575Z","iKey":"1a60808c-e79e-4613-8e2d-a1dc5da2812e","name":"Microsoft.ApplicationInsights.1a60808ce79e46138e2da1dc5da2812e.Message","tags":{"ai.user.id":"rBvKb1AELFhw2eMIpNKhqF","ai.session.id":"48sPaUnMsgKBa2CdjKTb2O","ai.device.id":"browser","ai.device.type":"Browser","ai.operation.name":"/zorg-regelen/zorgzoeker","ai.operation.id":"b52646232a7a47e18596b154344ccb86","ai.internal.sdkVersion":"javascript:3.4.1","ai.internal.snippet":"-"},"data":{"baseType":"MessageD
```
```
{"itemsReceived":1,"itemsAccepted":1,"appId":"4f0376cb-a1ad-461a-a675-ff518fd67457","errors":[]}
```

### POST 200 https://dc.services.visualstudio.com/v2/track (96 tekens)

Verzonden:
```
[{"time":"2026-11-25T13:38:44.575Z","iKey":"1a60808c-e79e-4613-8e2d-a1dc5da2812e","name":"Microsoft.ApplicationInsights.1a60808ce79e46138e2da1dc5da2812e.Message","tags":{"ai.user.id":"rBvKb1AELFhw2eMIpNKhqF","ai.session.id":"48sPaUnMsgKBa2CdjKTb2O","ai.device.id":"browser","ai.device.type":"Browser","ai.operation.name":"/zorg-regelen/zorgzoeker","ai.operation.id":"b52646232a7a47e18596b154344ccb86","ai.internal.sdkVersion":"javascript:3.4.1","ai.internal.snippet":"-"},"data":{"baseType":"MessageD
```
```
{"itemsReceived":3,"itemsAccepted":3,"appId":"4f0376cb-a1ad-461a-a675-ff518fd67457","errors":[]}
```

