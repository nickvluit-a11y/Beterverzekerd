# Concept: verzoek aan de NZa om toegang tot de open dataset wachttijden

*Status: concept, nog niet verstuurd. Nick verstuurt dit zelf (bijvoorbeeld via het contactformulier op nza.nl
of naar het algemene adres van de NZa).*

---

**Onderwerp:** Geautomatiseerde toegang tot de open dataset "Wachttijden medisch-specialistische zorg"

Geachte heer/mevrouw,

Ik werk aan **Beterverzekerd**, een onafhankelijk en niet-commercieel initiatief dat consumenten helpt
zorgpolissen te vergelijken op de **kwaliteit** van de zorg die verzekeraars inkopen, niet alleen op premie.
Daarvoor koppelen we openbare bronnen per ziekenhuislocatie: kwaliteitsindicatoren (Zorginzicht),
contractstatus en wachttijden. Uw dataset "Wachttijden medisch-specialistische zorg"
(puc.overheid.nl, PUC_651798_22) is daarbij de belangrijkste bron voor wachttijden.

We halen de dataset geautomatiseerd op, eens per twee weken, in lijn met uw publicatieritme. We
respecteren robots.txt, gebruiken een herkenbare user-agent
(`BeterverzekerdBot/0.1 (+https://github.com/nickvluit-a11y/beterverzekerd)`) en vragen één bestand per keer
op. Sinds kort krijgen we op puc.overheid.nl een HTTP 403, ook op robots.txt, en ook de paden onder
zorgbeeld.nza.nl/rest-doc/ geven een 403. Ik wil de blokkade niet omzeilen. Daarom vraag ik u:

1. Is geautomatiseerd ophalen van deze open dataset toegestaan? Zo ja, kunt u onze user-agent toestaan, of een
   vaste download-URL noemen die we daarvoor kunnen gebruiken?
2. Waar staat de actuele documentatie van de open API voor wachttijden (zorgbeeld.nza.nl)? Mogen wij die
   gebruiken, en zijn er voorwaarden (rate limits, bronvermelding)?

We tonen de wachttijden altijd met bronvermelding (NZa) en peildatum, met de kanttekening dat de cijfers
door zorgaanbieders zelf worden aangeleverd.

Met vriendelijke groet,

[naam]
Beterverzekerd
