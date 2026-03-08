## Why

Le panneau droit de la page d'attribution split-screen ne scrolle pas. Le formulaire d'attribution (select sous-traitant + pourcentage) est cache en dessous du tableau de repartition et inaccessible. Le CDT ne peut pas attribuer de BDC.

## What Changes

- Corriger le layout flex du panneau droit dans `attribution_split.html` pour que le scroll fonctionne
- Le `<div id="attribution-panel">` casse la chaine flex entre le `<form>` et le div scrollable interne

## Capabilities

### New Capabilities

(aucune)

### Modified Capabilities

(aucune — c'est un fix CSS/layout, pas un changement de spec)

## Impact

- `templates/bdc/attribution_split.html` : ajout classes flex sur `#attribution-panel`
- Aucun changement backend, aucune migration
