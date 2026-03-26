## ADDED Requirements

### Requirement: Toggle "Joindre le BDC" dans la barre d'onglets du viewer PDF
Un toggle "Joindre le BDC" SHALL etre present dans la barre d'onglets du viewer PDF de la page attribution split-screen. Il est actif par defaut.

#### Scenario: Toggle actif par defaut (chargement page)
- **WHEN** le CDT ouvre la page d'attribution
- **THEN** le toggle "Joindre le BDC" est actif, le bouton "Vue sous-traitant" est visible

#### Scenario: CDT desactive le toggle
- **WHEN** le CDT clique sur le toggle pour le desactiver
- **THEN** le bouton "Vue sous-traitant" disparait et la vue bascule automatiquement sur "PDF original" si elle etait sur "Vue sous-traitant"

#### Scenario: CDT reactive le toggle
- **WHEN** le CDT reactive le toggle
- **THEN** le bouton "Vue sous-traitant" reapparait

#### Scenario: Soumission du formulaire avec toggle actif
- **WHEN** le CDT soumet le formulaire avec le toggle actif
- **THEN** la fiche chantier PDF est jointe au mail envoye au ST

#### Scenario: Soumission du formulaire avec toggle inactif
- **WHEN** le CDT soumet le formulaire avec le toggle inactif
- **THEN** aucun PDF n'est joint au mail envoye au ST
