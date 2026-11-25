# Contracten Zilveren Kruis (handmatig)

De zorgzoeker van Zilveren Kruis beantwoordt alleen vragen van de eigen pagina, dus deze lijst wordt
met de hand gemaakt op https://www.zilverenkruis.nl/consumenten/zorgzoeker (zorg: Ziekenhuis,
basisverzekering: Basis Zeker, jaar 2027).

Bestandsnaam: `zk_contracten_<JJJJ-MM-DD>.csv` (de datum is de peildatum). Kolommen, gescheiden door `;`:

    naam;adres;postcode;plaats;status;omzetplafond

`status` is de tekst uit de zoeker, bijvoorbeeld `Contract: vergoed` of
`Nog geen contract: een deel niet vergoed`. `omzetplafond`: `ja` of leeg.
De data-run koppelt het nieuwste bestand automatisch aan de ziekenhuizen.
