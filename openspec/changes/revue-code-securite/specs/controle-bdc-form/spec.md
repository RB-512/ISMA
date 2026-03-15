## ADDED Requirements

### Requirement: Erreurs formulaire sidebar affichees
Quand le formulaire `BDCEditionForm` dans la sidebar est invalide, les erreurs de validation DOIVENT etre affichees a l'utilisateur via le message d'erreur de la sidebar.

#### Scenario: Formulaire sidebar invalide
- **WHEN** l'utilisateur soumet le formulaire sidebar avec des donnees invalides
- **THEN** un message d'erreur est affiche dans la sidebar avec le detail des erreurs

### Requirement: Pas de mutation sur GET dans sidebar_checklist
La vue `sidebar_checklist` NE DOIT PAS executer de transition de statut sur une requete GET. Les transitions DOIVENT etre declenchees uniquement par une requete POST.

#### Scenario: GET checklist sans items
- **WHEN** une requete GET est faite sur `sidebar_checklist` sans items de checklist
- **THEN** la vue affiche un formulaire de confirmation POST au lieu d'executer la transition directement

### Requirement: modifier_bdc restreint par statut
La vue `modifier_bdc` NE DOIT PAS permettre la modification d'un BDC dont le statut est `EN_COURS`, `A_FACTURER` ou `FACTURE`.

#### Scenario: Modification d'un BDC facture
- **WHEN** un utilisateur POST sur `modifier_bdc` pour un BDC au statut FACTURE
- **THEN** le systeme retourne une erreur 403 ou redirige avec un message d'erreur
