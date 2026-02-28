## Why

Après l'attribution (SPEC-006), le CDT doit envoyer au sous-traitant une version du BDC **sans les prix** (règle de confidentialité PRD §3.3). Actuellement, rien ne génère cette version terrain. Pour GDH, la page 2 du PDF original est déjà un bon d'intervention sans prix — il suffit de l'extraire. Pour ERILIA, les prix sont sur toutes les pages — il faut générer un PDF sans prix à partir des données du BDC.

## What Changes

- Ajout d'un service d'extraction de la page 2 d'un PDF GDH (PyMuPDF, déjà en dépendance)
- Ajout d'un service de génération de PDF terrain sans prix pour ERILIA (WeasyPrint, déjà en dépendance)
- Ajout d'un champ `pdf_terrain` sur le modèle `BonDeCommande` pour stocker le PDF généré
- Ajout d'un template HTML pour le rendu du BDC terrain ERILIA (converti en PDF via WeasyPrint)
- Ajout d'un bouton "Télécharger BDC terrain" sur la fiche détail, visible après attribution
- Génération automatique du PDF terrain lors de l'attribution (ou à la demande)

## Capabilities

### New Capabilities
- `generation-bdc-terrain`: Extraction page 2 GDH, génération PDF sans prix ERILIA, stockage et téléchargement du BDC terrain

### Modified Capabilities
- `fiche-detail-bdc`: Ajout d'un bouton "BDC terrain" visible quand le BDC est attribué (statut EN_COURS ou après)

## Impact

- `apps/bdc/models.py` : nouveau champ `pdf_terrain` (FileField)
- `apps/bdc/services.py` ou nouveau module `apps/bdc/terrain.py` : logique de génération
- `apps/bdc/views.py` : vue de téléchargement du PDF terrain
- `templates/bdc/terrain_erilia.html` : template HTML pour la génération PDF ERILIA
- `templates/bdc/detail.html` : bouton de téléchargement
- Dépendances existantes : `pymupdf` (extraction page), `weasyprint` (HTML → PDF)
- Migration Django pour le nouveau champ
