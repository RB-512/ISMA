## 1. Modèle et migration

- [x] 1.1 Ajouter `pdf_terrain` (FileField, nullable, blank, upload_to `bdc_terrain/`) sur `BonDeCommande` + créer la migration

## 2. Module terrain.py — génération PDF

- [x] 2.1 Créer `apps/bdc/terrain.py` avec exception `GenerationTerrainImpossible`
- [x] 2.2 Implémenter `_generer_terrain_gdh(bdc)` : extraction page 2 du PDF original via PyMuPDF, sauvegarde dans `pdf_terrain`
- [x] 2.3 Implémenter `_generer_terrain_erilia(bdc)` : rendu template HTML → PDF via WeasyPrint, sauvegarde dans `pdf_terrain`
- [x] 2.4 Implémenter `generer_pdf_terrain(bdc)` : dispatch selon `bdc.bailleur.code`, appelle GDH ou ERILIA (défaut)

## 3. Template HTML terrain ERILIA

- [x] 3.1 Créer `templates/bdc/terrain_erilia.html` : numéro BDC, adresse, programme, objet travaux, délai, occupant, prestations (désignation + qté + unité, SANS prix)

## 4. Intégration avec l'attribution

- [x] 4.1 Modifier `attribuer_st()` : appeler `generer_pdf_terrain(bdc)` après attribution, capturer les erreurs (non-bloquant, logger warning)
- [x] 4.2 Modifier `reattribuer_st()` : régénérer le PDF terrain après réattribution (même logique non-bloquante)

## 5. Vue et route de téléchargement

- [x] 5.1 Créer la vue `telecharger_terrain(pk)` : sert le `pdf_terrain` en téléchargement, 404 si absent
- [x] 5.2 Ajouter la route `<int:pk>/terrain/` dans `urls.py`

## 6. Template detail — bouton BDC terrain

- [x] 6.1 Modifier `templates/bdc/detail.html` : ajouter bouton "BDC terrain" dans l'en-tête quand `bdc.pdf_terrain` est renseigné

## 7. Tests

- [x] 7.1 Tests unitaires `_generer_terrain_gdh()` : extraction page 2 réussie, PDF 1 page → erreur
- [x] 7.2 Tests unitaires `_generer_terrain_erilia()` : PDF généré, pas de prix dans le contenu
- [x] 7.3 Tests unitaires `generer_pdf_terrain()` : dispatch GDH, dispatch ERILIA, bailleur inconnu → fallback ERILIA
- [x] 7.4 Tests intégration : attribution génère le PDF terrain automatiquement, réattribution régénère
- [x] 7.5 Tests vue `telecharger_terrain` : téléchargement OK, 404 si absent
- [x] 7.6 Tests template detail : bouton BDC terrain conditionnel

## 8. Validation

- [x] 8.1 Lancer `pytest` et `ruff check` — tous les tests passent, pas de lint
