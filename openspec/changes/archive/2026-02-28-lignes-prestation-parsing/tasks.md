## Tasks

### 1. GDH — Extraction des lignes de prestation

- [x] 1.1 Ajouter `_extraire_lignes_prestation(self, tables: list) -> list[dict]` dans `GDHParser` — identifier la row de prestation (après la row `P.U.H.T`), parser chaque ligne avec regex, concaténer les lignes de continuation
- [x] 1.2 Remplacer `"lignes_prestation": []` par `self._extraire_lignes_prestation(tables_p1)` dans `extraire()`
- [x] 1.3 Mettre à jour `test_gdh_parser.py` — ajouter la row de prestation dans `TABLE_P1`, modifier `test_extraire_lignes_prestation_vide` en `test_extraire_lignes_prestation` avec valeurs attendues
- [x] 1.4 Mettre à jour `test_gdh_parser_integration.py` — remplacer `test_lignes_prestation_vide` par `test_lignes_prestation` vérifiant 1 ligne avec `prix_unitaire=11.19`, `quantite=15.00`, `montant_ht=167.85`, `unite="m²"`

### 2. ERILIA — Extraction des lignes de prestation

- [x] 2.1 Ajouter `_extraire_lignes_prestation(self, tables: list) -> list[dict]` dans `ERILIAParser` — identifier la table contenant `ARTICLE DÉSIGNATION`, parser chaque ligne avec regex, concaténer les descriptions multi-lignes, ignorer les lignes `EDL :`
- [x] 2.2 Extraire les tables dans `extraire()` et remplacer `"lignes_prestation": []` par `self._extraire_lignes_prestation(tables_p1)`
- [x] 2.3 Mettre à jour `test_erilia_parser.py` — ajouter les données de table ERILIA dans le mock, modifier `test_extraire_lignes_prestation_vide` en `test_extraire_lignes_prestation` avec 3 lignes attendues
- [x] 2.4 Mettre à jour `test_erilia_parser_integration.py` — remplacer `test_lignes_prestation_vide` par `test_lignes_prestation` vérifiant 3 lignes avec codes PP4-31, PP4-33, PP4-43 et montants exacts

### 3. Validation

- [x] 3.1 Lancer `pytest` — tous les tests passent (unitaires + intégration)
- [x] 3.2 Lancer `ruff check` — aucune erreur
