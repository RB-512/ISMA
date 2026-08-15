## Why

L'envoi du PDF bailleur au sous-traitant est une usine a gaz : masquage de zones, filtrage de pages, config par bailleur. Ca casse regulierement (erreur 500 "Vue ST"), certains bailleurs n'ont pas de page terrain exploitable, et les prix sont parfois visibles. On remplace tout ca par une fiche chantier PDF generee a partir des donnees en base — simple, fiable, et identique pour tous les bailleurs.

## What Changes

- Nouveau service de generation d'une fiche chantier PDF (WeasyPrint/HTML→PDF) contenant : numero BDC, bailleur, adresse, residence, occupation, occupant (nom/tel), liste des prestations SANS prix, commentaire CDT, date RDV, delai
- Remplacement de la "Vue sous-traitant" (iframe PDF masque) par un apercu de la fiche generee
- Remplacement de la piece jointe email (PDF masque) par la fiche generee
- Suppression du systeme de masquage PDF (masquage_pdf.py, zones_masquage, pages_a_envoyer)

## Capabilities

### New Capabilities
- `fiche-chantier-pdf`: Generation d'une fiche chantier PDF a partir des donnees en base, sans prix, avec consignes CDT

### Modified Capabilities
- `notifications-email`: La piece jointe de l'email d'attribution devient la fiche chantier generee au lieu du PDF masque
- `attribution-bdc`: La "Vue sous-traitant" affiche la fiche generee au lieu du PDF masque

## Impact

- `apps/bdc/masquage_pdf.py` — supprime
- `apps/bdc/views.py` (pdf_masque_preview) — remplace par la fiche generee
- `apps/notifications/email.py` (_obtenir_pdf_masque) — remplace par generation fiche
- `templates/bdc/attribution_split.html` — iframe pointe vers la nouvelle fiche
- Config bailleur : champs `zones_masquage` et `pages_a_envoyer` deviennent obsoletes
- Nouvelle dependance : WeasyPrint (ou alternative HTML→PDF)
