## Context

Le template `_detail_sidebar.html` utilise `{% if is_cdt %}` pour afficher le bouton d'attribution en vert (actif) ou gris (desactive). Trois vues Django rendent ce template :

| Vue | Passe `is_cdt` ? |
|-----|-------------------|
| `_render_sidebar()` (L454) | Oui |
| `detail_sidebar()` (L495) | **Non** — bug |
| `sidebar_save_and_transition()` (L580) | **Non** — bug |

`detail_sidebar()` est appele au clic sur un BDC dans le dashboard (chargement HTMX de la sidebar). C'est le cas principal du bug.

## Goals / Non-Goals

**Goals:**
- Passer `is_cdt` dans le contexte des 2 vues manquantes

**Non-Goals:**
- Refactoriser les vues sidebar (la duplication du contexte existe deja, on ne la corrige pas ici)

## Decisions

Ajouter `"is_cdt": request.user.groups.filter(name="CDT").exists()` dans le dict de contexte des 2 vues. Pattern identique a `_render_sidebar()` qui le fait deja correctement.

## Risks / Trade-offs

Aucun risque — ajout d'une variable de contexte manquante, pattern deja etabli dans le code.
