## MODIFIED Requirements

### Requirement: Colonne adresse du relevé de facturation
Le relevé de facturation DOIT afficher la ville dans l'export PDF, en plus de l'adresse.

#### Scenario: Export PDF avec ville
- **WHEN** un utilisateur exporte le relevé en PDF
- **THEN** la colonne "Ville" DOIT être présente avec la valeur du champ `ville` du BDC
