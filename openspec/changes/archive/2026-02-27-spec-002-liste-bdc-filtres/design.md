## Context

L'application BDC Peinture a une vue `index` placeholder. La secrétaire et le CDT ont besoin d'un tableau de bord pour voir, filtrer et rechercher les BDC existants. Le modèle `BonDeCommande` est déjà complet avec statut, bailleur, adresse, etc. `django-filter` est déjà installé dans le projet (import présent dans `filters.py`).

## Goals / Non-Goals

**Goals:**
- Dashboard fonctionnel avec liste paginée des BDC
- Filtres par statut, bailleur, ville, plage de dates
- Recherche textuelle sur numéro BDC, adresse, occupant
- Compteurs par statut en haut du dashboard
- Navigation cohérente dans `base.html`

**Non-Goals:**
- Tri dynamique côté client (HTMX sera utilisé dans un futur change)
- Export CSV/Excel des résultats
- Filtres avancés (par sous-traitant, par montant)
- Vue kanban par statut

## Decisions

### D1 : django-filter pour les filtres
**Choix** : Utiliser `django_filters.FilterSet` avec `BonDeCommandeFilter`.
**Raison** : Déjà installé, pattern standard Django, intégration native avec les querysets. Pas besoin de réinventer un système de filtrage.
**Alternative rejetée** : Filtrage manuel via GET params — plus de code, moins maintenable.

### D2 : Recherche textuelle via Q objects
**Choix** : Champ de recherche libre traité via `Q(numero_bdc__icontains=q) | Q(adresse__icontains=q) | Q(occupant_nom__icontains=q)` dans la vue, pas dans le FilterSet.
**Raison** : django-filter ne gère pas nativement la recherche multi-champs avec un seul input. Un `CharFilter` avec `method=` custom est possible mais Q objects dans la vue est plus explicite.

### D3 : Pagination Django native
**Choix** : `django.core.paginator.Paginator` avec 25 items par page.
**Raison** : Suffisant pour le volume (50-150 BDC/mois). Pas besoin de pagination côté client ou infinite scroll.

### D4 : Compteurs par statut via agrégation
**Choix** : `BonDeCommande.objects.values('statut').annotate(count=Count('id'))` pour obtenir les compteurs en une seule requête.
**Raison** : Une seule requête DB au lieu de 5 COUNT séparés. Performance optimale.

### D5 : Template dashboard avec Tailwind
**Choix** : Template `bdc/liste.html` avec cards compteurs + table responsive + sidebar filtres.
**Raison** : Cohérent avec le design system existant (Tailwind + Alpine.js).

## Risks / Trade-offs

- **[Volume croissant]** → La pagination Django est suffisante jusqu'à ~10 000 BDC. Au-delà, envisager `select_related`/`prefetch_related` + index DB. Le `ordering = ["-created_at"]` existant sur le modèle assure un tri par défaut performant.
- **[Filtres combinés]** → Trop de filtres simultanés peuvent ralentir. Mitigation : index sur `statut`, `bailleur_id`, `ville` déjà implicites via les FK et le queryset.
