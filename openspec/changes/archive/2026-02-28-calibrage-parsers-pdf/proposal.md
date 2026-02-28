## Why

Les parsers GDH et ERILIA ont été écrits avec des patterns regex hypothétiques. L'analyse des vrais PDFs modèles (`docs/Modèle_bdc_GDH.pdf` et `docs/Modèle_bdc_ERILIA.pdf`) via pdfplumber révèle que **la quasi-totalité des patterns ne matchent pas** le texte réellement extrait. Sans calibrage, l'extraction retourne des champs vides pour chaque BDC uploadé.

## What Changes

- **Réécriture des regex GDH** : le numéro BDC est au format `n° 450056 du 09/02/2026` dans l'en-tête (pas "BDC n°"), la date est dans ce même en-tête, l'adresse est dans une cellule de table sans préfixe "Adresse :", les infos logement sont dans une ligne unique "Habitation n° … de type … Etage … porte …", l'objet travaux est dans l'en-tête sous "Bon de commande", les montants sont au format "Total HT 167.85 €" (avec point décimal).
- **Réécriture des regex ERILIA** : le docstring indiquait "1 page" mais le vrai PDF a 2 pages, le numéro est "N° 2026 20205" après "BON DE TRAVAUX", la date est "Édité le\n06-02-2026" en page 2, l'adresse est préfixée "ADRESSE" (majuscules), le programme est "Programme 1398 …", l'émetteur est "ÉMETTEUR NOM Tél …" sur une ligne.
- **Réécriture de `_extraire_lignes`** pour les deux parsers : les tables pdfplumber ne sont PAS au format 5 colonnes (Désignation/Qté/Unité/PU/Montant). GDH a des tables 2 colonnes avec des données mélangées. ERILIA a une table 1 colonne avec prestations fusionnées. Il faut un parsing textuel des lignes de prestation.
- **Tests d'intégration avec vrais PDFs** : ajout de tests exécutant l'extraction sur les PDFs modèles réels dans `docs/`, vérifiant les valeurs attendues.

## Capabilities

### New Capabilities
_(aucune)_

### Modified Capabilities
- `extraction-pdf-gdh`: Tous les patterns regex sont recalibrés sur le vrai format pdfplumber du PDF GDH modèle. L'extraction des lignes passe d'une approche table 5 colonnes à un parsing textuel.
- `extraction-pdf-erilia`: Tous les patterns regex sont recalibrés sur le vrai format pdfplumber du PDF ERILIA modèle. Le format passe de 1 page à 2 pages. L'extraction des lignes passe à un parsing textuel.

## Impact

- **Code modifié** : `apps/pdf_extraction/gdh_parser.py`, `apps/pdf_extraction/erilia_parser.py`
- **Tests modifiés** : `tests/test_bdc/test_gdh_parser.py`, `tests/test_bdc/test_erilia_parser.py` (ajout de tests d'intégration avec vrais PDFs)
- **Aucune dépendance ajoutée** : pdfplumber reste le seul extracteur
- **Aucun changement de modèle** : le dict de sortie garde la même structure
