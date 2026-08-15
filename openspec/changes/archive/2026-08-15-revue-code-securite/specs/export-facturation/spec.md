## ADDED Requirements

### Requirement: Export POST utilise les filtres
La vue `export_facturation` en methode POST DOIT appliquer les filtres selectionnes par l'utilisateur (statut, sous-traitant, dates) au queryset exporte.

#### Scenario: Export avec filtre sous-traitant
- **WHEN** l'utilisateur selectionne un sous-traitant dans le filtre puis clique Exporter
- **THEN** le fichier Excel ne contient que les BDC attribues a ce sous-traitant

## MODIFIED Requirements

### Requirement: Filtres par date
Les filtres `date_du` et `date_au` sur le dashboard et l'export DOIVENT utiliser `date__gte` et `date__lte` pour comparer uniquement la partie date du champ `created_at` (DateTimeField), incluant ainsi tous les records de la journee de debut et de fin.

#### Scenario: Filtre date_au inclut la journee entiere
- **WHEN** l'utilisateur filtre avec `date_au = 2026-03-15`
- **THEN** les BDC crees le 15 mars a 23h59 sont inclus dans les resultats
