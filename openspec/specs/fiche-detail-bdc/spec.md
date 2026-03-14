## MODIFIED Requirements

### Requirement: La fiche détail utilise le design system Isma
La fiche détail BDC SHALL utiliser les cards, couleurs, typographie et espacements du design system Isma. Les sections (Localisation, Travaux, Contacts, Prestations, Historique) SHALL être des cards avec le style surface-card. Les boutons d'action SHALL utiliser les couleurs du design system. Les numéros BDC et montants SHALL utiliser la font mono. Le tout SHALL supporter le dark mode.

#### Scenario: Fiche détail en light mode
- **WHEN** un utilisateur accède à la fiche détail d'un BDC en mode light
- **THEN** les cards utilisent le fond surface-card light, les textes sont en primary, les boutons utilisent les couleurs d'action

#### Scenario: Fiche détail en dark mode
- **WHEN** un utilisateur accède à la fiche détail d'un BDC en mode dark
- **THEN** les cards utilisent le fond surface-card dark, les textes sont clairs, le contraste est maintenu

### Requirement: La secrétaire peut éditer les champs manuels depuis la fiche détail
La fiche détail SHALL afficher un formulaire d'édition pour les champs manuels : `occupation` (select vacant/occupé), `modalite_acces` (textarea), `rdv_pris` (checkbox), `rdv_date` (datetime), `notes` (textarea). Le formulaire SHALL être visible uniquement pour les utilisateurs du groupe "Secretaire". Tous les widgets SHALL utiliser le style du design system Isma. La soumission SHALL sauvegarder les champs et enregistrer une action MODIFICATION dans l'historique.

#### Scenario: Affichage du formulaire pour une secrétaire
- **WHEN** un utilisateur du groupe "Secretaire" accède à la fiche détail
- **THEN** le formulaire d'édition des champs manuels est affiché avec les widgets stylisés design system Isma

#### Scenario: Formulaire masqué pour un non-secrétaire
- **WHEN** un utilisateur authentifié hors groupe "Secretaire" accède à la fiche détail
- **THEN** les champs manuels sont affichés en lecture seule, sans formulaire d'édition

### Requirement: Affichage contacts occupant
Le système NE DOIT PAS afficher le bloc contact "Occupant" lorsque le champ Occupation est vide.

#### Scenario: Occupation non renseignée avec données occupant
- **WHEN** `occupation` est vide mais `occupant_nom` contient une valeur
- **THEN** le bloc "Occupant" NE DOIT PAS être affiché
