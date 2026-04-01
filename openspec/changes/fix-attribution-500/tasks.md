## 1. Correction service attribution

- [x] 1.1 Dans `bdc-peinture/apps/bdc/services.py`, ajouter `if pourcentage is None: return None` en tête de `_calculer_montant_st` (après le guard sur `montant_ht`)

## 2. Alignement vue attribution_partial

- [x] 2.1 Dans `bdc-peinture/apps/bdc/views.py`, lire `joindre_bdc = request.POST.get("joindre_bdc") == "on"` dans `attribution_partial` (POST branch)
- [x] 2.2 Passer `joindre_bdc=joindre_bdc` aux appels `attribuer_st()` et `reattribuer_st()` dans `attribution_partial`

## 3. Tests

- [x] 3.1 Lancer `uv run pytest apps/bdc/ -v` et vérifier qu'aucun test ne régresse
- [x] 3.2 Vérifier manuellement : attribution en mode forfait sans lignes ne doit plus produire de 500
