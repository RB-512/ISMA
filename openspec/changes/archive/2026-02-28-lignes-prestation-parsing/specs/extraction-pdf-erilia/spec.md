## ADDED Requirements

### Requirement: ERILIAParser extrait les lignes de prestation depuis la table PDF
`ERILIAParser.extraire()` SHALL retourner dans `lignes_prestation` une liste de dicts contenant les champs `code`, `designation`, `unite`, `quantite`, `prix_unitaire`, `montant_ht`. Chaque dict correspond à une ligne de prestation extraite depuis la table 1 de la page 1. Les lignes de continuation de désignation SHALL être concaténées. Les lignes commençant par `EDL :` SHALL être ignorées.

#### Scenario: Extraction de 3 lignes de prestation ERILIA
- **WHEN** la table page 1 contient les articles PP4-31, PP4-33, PP4-43
- **THEN** `lignes_prestation` contient 3 dicts avec les codes respectifs `"PP4-31"`, `"PP4-33"`, `"PP4-43"`

#### Scenario: Extraction des valeurs d'une ligne ERILIA
- **WHEN** la table contient `PP4-31 Peinture finition A sur murs, plafond, FOR 1,00 180,27 198,30`
- **THEN** `lignes_prestation[0]` contient `code` vaut `"PP4-31"`, `designation` contenant `"Peinture finition A sur murs, plafond, boiseries et métalleries - WC"`, `unite` vaut `"FOR"`, `quantite` vaut `Decimal("1.00")`, `prix_unitaire` vaut `Decimal("180.27")`, `montant_ht` vaut `Decimal("180.27")`

#### Scenario: Concaténation des lignes de continuation ERILIA
- **WHEN** une ligne de prestation est suivie par `boiseries et métalleries - WC`
- **THEN** ce texte est concaténé à la `designation` de la ligne précédente

#### Scenario: Lignes EDL ignorées
- **WHEN** une ligne commence par `EDL :` dans la cellule de table
- **THEN** elle est ignorée et non ajoutée aux lignes de prestation ni concaténée à la désignation

#### Scenario: Table sans lignes de prestation identifiables
- **WHEN** la table page 1 ne contient aucune row matchant le pattern ERILIA
- **THEN** `lignes_prestation` est une liste vide `[]`

#### Scenario: Champ ordre incrémenté par ligne
- **WHEN** la table contient N lignes de prestation
- **THEN** chaque dict a un champ `ordre` allant de `0` à `N-1`

### Requirement: Test d'intégration ERILIA vérifie les lignes de prestation
Le test d'intégration sur `docs/Modèle_bdc_ERILIA.pdf` SHALL vérifier les lignes de prestation extraites.

#### Scenario: Extraction du PDF modèle ERILIA retourne les lignes correctes
- **WHEN** `ERILIAParser("docs/Modèle_bdc_ERILIA.pdf").extraire()` est appelé
- **THEN** `lignes_prestation` contient 3 lignes, avec `lignes_prestation[0]["code"]` vaut `"PP4-31"`, `lignes_prestation[0]["prix_unitaire"]` vaut `Decimal("180.27")`, `lignes_prestation[2]["code"]` vaut `"PP4-43"`, `lignes_prestation[2]["montant_ht"]` vaut `Decimal("578.03")`
