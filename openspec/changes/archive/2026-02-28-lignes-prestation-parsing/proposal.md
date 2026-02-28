## Why

Les parsers GDH et ERILIA retournent actuellement `lignes_prestation: []`. La vue `creer_bdc` consomme déjà ces lignes pour créer des `LignePrestation` en base, mais elles ne sont jamais extraites du PDF. Sans ces données, la secrétaire doit saisir manuellement chaque ligne de prestation (désignation, quantité, unité, prix unitaire, montant). L'extraction automatique complète le pipeline PDF → BDC.

## What Changes

- Implémentation de `_extraire_lignes_prestation()` dans `GDHParser` — parse la table page 1, row contenant les colonnes `P.U.H.T (€) Quantité Montant HT (€) TVA`
- Implémentation de `_extraire_lignes_prestation()` dans `ERILIAParser` — parse la table page 1, section `ARTICLE DÉSIGNATION UNITÉ QUANTITÉ PRIX UNITAIRE H.T. TOTAL T.T.C.`
- Chaque ligne retourne un dict `{code, designation, unite, quantite, prix_unitaire, montant_ht}` compatible avec le modèle `LignePrestation`
- Mise à jour des tests unitaires et d'intégration (remplacement des `assert == []` par les valeurs réelles)

## Capabilities

### New Capabilities

_(aucune — les parsers et le modèle LignePrestation existent déjà)_

### Modified Capabilities

- `extraction-pdf-gdh`: Ajout de l'extraction des lignes de prestation depuis la table GDH
- `extraction-pdf-erilia`: Ajout de l'extraction des lignes de prestation depuis la table ERILIA

## Impact

- `apps/pdf_extraction/gdh_parser.py` — ajout de `_extraire_lignes_prestation()`
- `apps/pdf_extraction/erilia_parser.py` — ajout de `_extraire_lignes_prestation()`
- `tests/test_pdf_extraction/test_gdh_parser.py` — mise à jour mock + tests lignes
- `tests/test_pdf_extraction/test_erilia_parser.py` — mise à jour mock + tests lignes
- `tests/test_pdf_extraction/test_gdh_parser_integration.py` — tests lignes réelles
- `tests/test_pdf_extraction/test_erilia_parser_integration.py` — tests lignes réelles
- Aucune migration Django requise (le modèle `LignePrestation` existe déjà)
- Aucune modification de la vue `creer_bdc` (elle consomme déjà `lignes_prestation`)
