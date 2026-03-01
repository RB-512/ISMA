# Page attribution split-screen

## Resume

Creer une page d'attribution split-screen identique au pattern de la page controle : PDF a gauche (60%), panneau d'action a droite (40%). Le panneau droit contient un resume compact du BDC, le tableau de repartition ST avec selecteur de periode/N-1, et le formulaire d'attribution. Sert a la fois pour l'attribution (A_FAIRE) et la reattribution (EN_COURS).

## Decisions

- **Pattern** : split-screen comme controle.html (PDF gauche 60%, panneau droit 40%)
- **Scope** : attribution + reattribution (meme page, titre et bouton adaptes)
- **Panneau droit** : resume BDC compact + selecteur periode + tableau repartition ST + formulaire
- **HTMX** : le selecteur de periode recharge uniquement le bloc repartition (pas toute la page)
- **Boutons sticky** : Attribuer/Reattribuer + Annuler en bas du panneau
- **Redirection** : tous les boutons Attribuer/Reattribuer (sidebar, detail, dashboard) pointent vers cette page
- **Ancienne page** : attribuer.html conservee comme fallback mais plus liee

## Design UI

```
+-- Header -------------------------------------------------------------------+
|  <- retour    BDC 450057    [A attribuer]    GDH                            |
+-----------------------------------------------------------------------------+

+-- PDF (60%) ----------------------+-- Panneau droit (40%) ------------------+
|                                   |  Resume BDC                             |
|                                   |  Adresse, travaux, occupation, montant  |
|   iframe PDF ou placeholder       |                                         |
|                                   |  [Sem] [Mois] [Tri] [Annee]            |
|                                   |  Du [____] Au [____] [Appliquer]       |
|                                   |                                         |
|                                   |  Repartition ST                         |
|                                   |  ST         BDC  Montant  N-1          |
|                                   |  Dupont       3   12 400   2           |
|                                   |  Martin       1    4 200   3           |
|                                   |                                         |
|                                   |  Sous-traitant: [v Choisir]            |
|                                   |  Pourcentage:   [65.00] %              |
|                                   +----------------------------------------+
|                                   |  [Attribuer]       [Annuler]    sticky |
+-----------------------------------+----------------------------------------+
```

## Fichiers a modifier

| Fichier | Action |
|---|---|
| `templates/bdc/attribution_split.html` | Nouveau template split-screen |
| `templates/bdc/partials/_attribution_panel.html` | Nouveau partial panneau droit (resume + repartition + form) |
| `apps/bdc/views.py` | Nouvelle vue `attribution_split` |
| `apps/bdc/urls.py` | Nouvelle URL |
| `templates/bdc/detail.html` | Boutons pointent vers attribution_split |
| `templates/bdc/_detail_sidebar.html` | Bouton pointe vers attribution_split |
| `tests/test_bdc/test_attribution.py` | Nouveaux tests |

## Backend

### Vue `attribution_split(request, pk)`

- GET : render split-screen avec resume BDC + repartition ST + formulaire vide (ou pre-rempli si reattribution)
- POST : traiter l'attribution, redirect vers detail en cas de succes, re-render avec erreurs sinon
- Reutilise les helpers existants : `_get_repartition_st`, `_parse_periode_params`, `_attach_n1_data`
- Accepte les query params de periode pour le rechargement HTMX du tableau
- Si `HX-Request` header present sur GET : retourne seulement le partial `_attribution_panel.html`

### URL

`path("<int:pk>/attribution/", views.attribution_split, name="attribution_split")`

## Tests

- `test_get_affiche_split_screen` : page 200 avec PDF iframe et formulaire
- `test_post_valide_attribue` : attribution OK, redirect vers detail
- `test_post_invalide_reaffiche` : erreurs de formulaire affichees
- `test_reattribution_pre_rempli` : BDC EN_COURS, formulaire pre-rempli
- `test_htmx_retourne_partial` : avec HX-Request, pas de <html> dans la reponse
- `test_acces_secretaire_interdit` : 403 pour non-CDT
- `test_repartition_st_presente` : le tableau de repartition est dans la reponse
