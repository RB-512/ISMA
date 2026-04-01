## Why

Le conducteur de travaux rencontre régulièrement une erreur 500 lors de l'attribution d'un BDC à un sous-traitant. L'analyse du code révèle un bug dans `_calculer_montant_st` : si le mode est `forfait` mais qu'aucune ligne n'est transmise, la fonction est appelée avec `pourcentage=None` alors que `montant_ht` est renseigné, provoquant un `TypeError`.

## What Changes

- Correction de `_calculer_montant_st` dans `services.py` : guard sur `pourcentage is None` → retourne `None` au lieu de crasher
- Alignement de `attribution_partial` avec `attribution_split` : passage du paramètre `joindre_bdc` manquant dans la vue HTMX inline

## Capabilities

### New Capabilities

*(aucune)*

### Modified Capabilities

- `attribution-bdc` : Correction du comportement en mode forfait avec lignes vides, et alignement des deux vues d'attribution sur le passage de `joindre_bdc`

## Impact

- `bdc-peinture/apps/bdc/services.py` : fonction `_calculer_montant_st`
- `bdc-peinture/apps/bdc/views.py` : vue `attribution_partial` (ajout `joindre_bdc`)
- Aucune migration, aucun impact UI
