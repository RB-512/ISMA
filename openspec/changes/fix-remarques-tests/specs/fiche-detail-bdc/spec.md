## MODIFIED Requirements

### Requirement: Affichage contacts occupant
Le système NE DOIT PAS afficher le bloc contact "Occupant" lorsque le champ Occupation est vide.

#### Scenario: Occupation non renseignée avec données occupant
- **WHEN** `occupation` est vide mais `occupant_nom` contient une valeur
- **THEN** le bloc "Occupant" NE DOIT PAS être affiché
