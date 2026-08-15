## Why

La vue `detail_sidebar` ne transmet pas la variable `is_cdt` au template `_detail_sidebar.html`. Le template teste `{% if is_cdt %}` pour afficher le bouton d'attribution actif, mais la variable etant absente du contexte, elle vaut toujours `False`. Le bouton est donc systematiquement grise pour tous les utilisateurs, y compris les CDT. C'est une regression.

## What Changes

- Ajouter `is_cdt` au contexte de la vue `detail_sidebar()` dans `apps/bdc/views.py`
- Verifier que les autres vues retournant `_detail_sidebar.html` passent aussi `is_cdt`

## Capabilities

### New Capabilities

(aucune)

### Modified Capabilities

(aucune — correction de bug, pas de changement de spec)

## Impact

- `apps/bdc/views.py` : vue `detail_sidebar()` (et potentiellement `sidebar_action()`)
- Template `_detail_sidebar.html` : aucun changement necessaire (le template est deja correct)
