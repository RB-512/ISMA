## Context

La page d'attribution (`attribution_split.html`) utilise un layout split-screen : PDF a gauche (60%), panneau d'attribution a droite (40%). Le panneau droit contient un resume BDC, un tableau de repartition ST, et le formulaire d'attribution en bas. Le contenu depasse la hauteur visible mais le scroll ne fonctionne pas.

Cause racine : `<div id="attribution-panel">` est un div neutre entre le `<form class="h-full flex flex-col">` et le `<div class="flex-1 overflow-y-auto">` du partial. Sans classes flex, il casse la propagation de la contrainte de hauteur.

## Goals / Non-Goals

**Goals:**
- Rendre le panneau droit scrollable pour acceder au formulaire d'attribution
- Fix minimal, une seule ligne CSS

**Non-Goals:**
- Refonte du layout de la page d'attribution
- Changement de fonctionnalite

## Decisions

**Ajouter `class="flex-1 overflow-hidden"` sur `#attribution-panel`**

Cela permet :
- `flex-1` : le div prend tout l'espace restant dans le flex column du form
- `overflow-hidden` : contraint la hauteur pour que le `overflow-y-auto` enfant declenche le scroll

Alternative ecartee : deplacer le contenu du partial directement dans le template — casserait le rechargement HTMX du panneau.

## Risks / Trade-offs

Aucun risque identifie. Fix CSS pur, aucun impact fonctionnel.
