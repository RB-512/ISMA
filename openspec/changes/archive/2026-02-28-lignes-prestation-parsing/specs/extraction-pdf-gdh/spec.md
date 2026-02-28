## ADDED Requirements

### Requirement: GDHParser extrait les lignes de prestation depuis la table PDF
`GDHParser.extraire()` SHALL retourner dans `lignes_prestation` une liste de dicts contenant les champs `designation`, `unite`, `quantite`, `prix_unitaire`, `montant_ht`. Chaque dict correspond à une ligne de prestation extraite depuis la table de la page 1. Les lignes de continuation de désignation SHALL être concaténées à la ligne précédente.

#### Scenario: Extraction d'une ligne de prestation GDH standard
- **WHEN** la table page 1 contient une row avec `M-P : préparation et mis (PS1402) 11.19 15.00 (m²) 167.85 10.00%`
- **THEN** `lignes_prestation[0]` contient `designation` contenant `"préparation et mise en peinture"`, `prix_unitaire` vaut `Decimal("11.19")`, `quantite` vaut `Decimal("15.00")`, `unite` vaut `"m²"`, `montant_ht` vaut `Decimal("167.85")`

#### Scenario: Concaténation de la ligne de continuation de désignation
- **WHEN** la cellule contient `M-P : préparation et mis (PS1402) 11.19 15.00 (m²) 167.85 10.00%\nM-P : préparation et mise en peinture`
- **THEN** la `designation` de la ligne est `"M-P : préparation et mise en peinture"` (ligne complète utilisée)

#### Scenario: Table sans lignes de prestation identifiables
- **WHEN** la table page 1 ne contient aucune row matchant le pattern de prestation
- **THEN** `lignes_prestation` est une liste vide `[]`

#### Scenario: Champ ordre incrémenté par ligne
- **WHEN** la table contient N lignes de prestation
- **THEN** chaque dict a un champ `ordre` allant de `0` à `N-1`

### Requirement: Test d'intégration GDH vérifie les lignes de prestation
Le test d'intégration sur `docs/Modèle_bdc_GDH.pdf` SHALL vérifier les lignes de prestation extraites.

#### Scenario: Extraction du PDF modèle GDH retourne les lignes correctes
- **WHEN** `GDHParser("docs/Modèle_bdc_GDH.pdf").extraire()` est appelé
- **THEN** `lignes_prestation` contient 1 ligne avec `prix_unitaire` vaut `Decimal("11.19")`, `quantite` vaut `Decimal("15.00")`, `montant_ht` vaut `Decimal("167.85")`, `unite` contient `"m²"`
