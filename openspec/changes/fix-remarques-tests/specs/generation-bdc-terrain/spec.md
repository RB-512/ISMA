## MODIFIED Requirements

### Requirement: Localisation sur fiche chantier sous-traitant
La fiche chantier ST DOIT afficher étage et porte en plus du numéro de logement.

#### Scenario: Logement avec étage et porte
- **WHEN** `logement_etage` et `logement_porte` sont renseignés
- **THEN** afficher "N° — Étage X / Porte Y"
