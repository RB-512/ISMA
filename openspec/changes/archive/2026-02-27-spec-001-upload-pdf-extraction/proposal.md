## Why

Sans import de PDF, aucun BDC ne peut exister dans le système : c'est la porte d'entrée unique du workflow. SPEC-001 implémente la réception d'un PDF bailleur, son extraction automatique et la création du BDC via formulaire pré-rempli.

## What Changes

- Ajout d'une page d'upload de PDF (interface secrétaire)
- Implémentation de la détection automatique du type de bailleur (GDH vs ERILIA)
- Implémentation de `GDHParser` : extraction des données structurées depuis le PDF GDH (2 pages)
- Implémentation de `ERILIAParser` : extraction des données depuis le PDF ERILIA (1 page, prix inclus)
- Formulaire de création de BDC pré-rempli depuis les données extraites, avec validation manuelle
- Détection de doublon sur le numéro BDC (blocage si déjà existant)
- Stockage du PDF original et accès en consultation

## Capabilities

### New Capabilities

- `upload-pdf` : page d'upload du PDF bailleur avec feedback d'extraction (détection type, succès/erreur)
- `extraction-pdf-gdh` : parser GDH qui extrait les données structurées (numéro, adresse, travaux, montants, lignes) depuis un PDF GDH
- `extraction-pdf-erilia` : parser ERILIA qui extrait les mêmes données depuis un PDF ERILIA (format différent)
- `formulaire-creation-bdc` : formulaire pré-rempli depuis l'extraction, avec complétion manuelle (occupation, accès, RDV), détection doublon, validation et création du BDC en base

### Modified Capabilities

- `modeles-donnees-bdc` : aucun changement de modèle requis (les stubs `GDHParser`, `ERILIAParser`, `detecter_parser` et `BonDeCommande.pdf_original` existent déjà)

## Impact

- `apps/pdf_extraction/gdh_parser.py` — implémentation complète (remplace le stub)
- `apps/pdf_extraction/erilia_parser.py` — implémentation complète (remplace le stub)
- `apps/pdf_extraction/detector.py` — implémentation de `detecter_parser()`
- `apps/bdc/views.py` — ajout des vues `upload_pdf` et `creer_bdc`
- `apps/bdc/forms.py` — nouveau formulaire `BonDeCommandeForm`
- `apps/bdc/urls.py` — routes `/upload/` et `/nouveau/`
- `templates/bdc/upload.html` — formulaire d'upload
- `templates/bdc/creer_bdc.html` — formulaire de création pré-rempli
- Dépendances : `pdfplumber>=0.11`, `pymupdf>=1.24` (déjà dans pyproject.toml)
