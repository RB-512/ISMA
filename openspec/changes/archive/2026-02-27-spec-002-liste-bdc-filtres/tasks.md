## 1. FilterSet django-filter

- [x] 1.1 Implémenter `BonDeCommandeFilter` dans `apps/bdc/filters.py` avec filtres : `statut` (ChoiceFilter), `bailleur` (ModelChoiceFilter), `ville` (CharFilter icontains), `date_du` (DateFilter gte sur created_at), `date_au` (DateFilter lte sur created_at)
- [x] 1.2 Écrire les tests unitaires du FilterSet (test chaque filtre individuellement + combinaison)

## 2. Vue liste_bdc

- [x] 2.1 Remplacer la vue `index` par `liste_bdc` dans `apps/bdc/views.py` : queryset avec `select_related("bailleur")`, application du FilterSet, recherche textuelle via Q objects (numero_bdc, adresse, occupant_nom), pagination 25/page
- [x] 2.2 Ajouter les compteurs par statut via `values('statut').annotate(count=Count('id'))` dans le context
- [x] 2.3 Mettre à jour la route `index` dans `apps/bdc/urls.py` pour pointer vers `liste_bdc`

## 3. Template liste.html

- [x] 3.1 Créer `templates/bdc/liste.html` : cards compteurs par statut en haut, formulaire de filtres (sidebar ou inline), champ recherche, tableau des BDC avec colonnes (N°, Bailleur, Adresse, Ville, Statut badge, Date), lignes cliquables vers le détail
- [x] 3.2 Ajouter la pagination en bas du tableau (précédent/suivant/numéros de page) avec conservation des paramètres de filtre dans les liens
- [x] 3.3 Afficher un message "Aucun bon de commande trouvé" avec lien vers upload quand la liste est vide

## 4. Navigation base.html

- [x] 4.1 Mettre à jour `templates/base.html` : ajouter lien "Tableau de bord" → `/bdc/` et lien "Upload PDF" → `/bdc/upload/` dans la barre de navigation

## 5. Tests

- [x] 5.1 Tests vue liste_bdc : accès authentifié, redirection non-auth, liste vide, liste avec données, pagination page 2
- [x] 5.2 Tests filtres dans la vue : filtre statut, filtre bailleur, filtre ville, filtre plage dates, recherche textuelle, combinaison filtres + recherche
- [x] 5.3 Tests compteurs : vérifier que le context contient les bons compteurs par statut
- [x] 5.4 Vérifier 0 erreur ruff + tous les tests passent
