## Why

La vue `index` actuelle retourne un simple placeholder texte. La secrétaire et le CDT n'ont aucun moyen de voir la liste des BDC existants, filtrer par statut/bailleur, ni rechercher un BDC spécifique. Sans tableau de bord, l'application est inutilisable au quotidien après la création d'un BDC.

## What Changes

- Remplacer le placeholder `index` par un vrai tableau de bord listant tous les BDC
- Ajouter un système de filtres (statut, bailleur, ville, date) avec django-filter
- Ajouter une recherche textuelle (numéro BDC, adresse, occupant)
- Paginer les résultats (25 par page)
- Afficher des compteurs par statut en en-tête du dashboard
- Adapter la navigation (`base.html`) avec des liens vers upload et dashboard

## Capabilities

### New Capabilities
- `dashboard-liste-bdc`: Tableau de bord principal avec liste paginée des BDC, filtres multi-critères, recherche textuelle et compteurs par statut

### Modified Capabilities
- `base-template-ui`: Ajout des liens de navigation (Upload PDF, Tableau de bord) dans la barre de navigation

## Impact

- `apps/bdc/views.py` : remplacement de la vue `index` par `liste_bdc`
- `apps/bdc/filters.py` : implémentation du `BonDeCommandeFilter` (django-filter)
- `templates/bdc/liste.html` : nouveau template pour le dashboard
- `templates/base.html` : mise à jour de la navigation
- `apps/bdc/urls.py` : ajustement de la route index
- Tests : nouveaux tests pour la vue liste, les filtres et la pagination
