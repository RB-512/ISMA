## MODIFIED Requirements

### Requirement: Le CDT peut valider la réalisation d'un BDC
Le système SHALL permettre de marquer un BDC EN_COURS comme réalisé via `valider_realisation(bdc, utilisateur, date_intervention)`. La date d'intervention SHALL être obligatoire et NE DOIT PAS être postérieure à la date du jour. Elle SHALL être enregistrée dans `date_realisation`. Le statut SHALL passer à A_FACTURER. L'action VALIDATION SHALL être tracée dans l'historique. Sans date valide, le statut NE DOIT PAS changer.

#### Scenario: Validation réalisation réussie
- **WHEN** l'utilisateur appelle `valider_realisation()` sur un BDC EN_COURS avec une date d'intervention passée ou du jour
- **THEN** le statut passe à A_FACTURER, `date_realisation` vaut la date saisie, une action VALIDATION est tracée dans l'historique

#### Scenario: Date d'intervention manquante
- **WHEN** l'utilisateur valide la réalisation sans date d'intervention
- **THEN** une erreur `BDCIncomplet` est levée et le BDC reste EN_COURS

#### Scenario: Date d'intervention future
- **WHEN** l'utilisateur valide la réalisation avec une date postérieure à aujourd'hui
- **THEN** une erreur `BDCIncomplet` est levée et le BDC reste EN_COURS

#### Scenario: Validation refuse si pas EN_COURS
- **WHEN** l'utilisateur appelle `valider_realisation()` sur un BDC qui n'est pas EN_COURS
- **THEN** une erreur `TransitionInvalide` est levée

#### Scenario: Historique de validation
- **WHEN** la validation réussit
- **THEN** l'historique contient une entrée VALIDATION avec les détails (date_realisation)

### Requirement: Le CDT peut passer un BDC en facturation
Le système SHALL permettre de passer un BDC A_FACTURER au statut FACTURE via `valider_facturation(bdc, utilisateur, numero_facture, date_facturation)`. Le n° de facture et la date de facturation SHALL être obligatoires. Le n° de facture SHALL être unique parmi les BDC. La date de facturation NE DOIT PAS être postérieure à la date du jour ni antérieure à la date d'intervention. L'action FACTURATION SHALL être tracée dans l'historique avec le n° et la date. Sans données valides, le statut NE DOIT PAS changer.

#### Scenario: Passage en facturation réussi
- **WHEN** l'utilisateur appelle `valider_facturation()` sur un BDC A_FACTURER avec un n° de facture inédit et une date valide
- **THEN** le statut passe à FACTURE, `numero_facture` et `date_facturation` sont enregistrés, une action FACTURATION est tracée dans l'historique

#### Scenario: N° ou date de facture manquant
- **WHEN** l'utilisateur passe en facturation sans n° de facture ou sans date de facturation
- **THEN** une erreur `BDCIncomplet` est levée et le BDC reste A_FACTURER

#### Scenario: N° de facture déjà utilisé
- **WHEN** le n° de facture saisi est déjà enregistré sur un autre BDC
- **THEN** une erreur `BDCIncomplet` indiquant le BDC concerné est levée et le BDC reste A_FACTURER

#### Scenario: Date de facturation incohérente
- **WHEN** la date de facturation est future ou antérieure à la date d'intervention
- **THEN** une erreur `BDCIncomplet` est levée et le BDC reste A_FACTURER

#### Scenario: Facturation refuse si pas A_FACTURER
- **WHEN** l'utilisateur appelle `valider_facturation()` sur un BDC qui n'est pas A_FACTURER
- **THEN** une erreur `TransitionInvalide` est levée

## ADDED Requirements

### Requirement: Les transitions vers À facturer et Facturé passent obligatoirement par la saisie
Le changement de statut générique (`changer_statut`) NE DOIT PAS permettre les transitions EN_COURS → A_FACTURER et A_FACTURER → FACTURE. Ces transitions SHALL passer par `valider_realisation` et `valider_facturation`. L'interface (sidebar et fiche détail) SHALL demander la date d'intervention, puis le n° et la date de facture, avant de confirmer la transition, y compris quand une checklist de transition est configurée.

#### Scenario: Transition générique refusée
- **WHEN** `changer_statut()` est appelé pour passer un BDC EN_COURS en A_FACTURER, ou A_FACTURER en FACTURE
- **THEN** une erreur `BDCIncomplet` est levée et le statut ne change pas

#### Scenario: Saisie depuis la sidebar
- **WHEN** l'utilisateur clique sur « Valider » dans la sidebar d'un BDC EN_COURS
- **THEN** un panneau demande la date d'intervention (pré-remplie à aujourd'hui) et, s'il en existe, les points de contrôle, avant confirmation

#### Scenario: Erreur de saisie réaffichée
- **WHEN** la saisie est refusée (champ manquant, date invalide, n° déjà utilisé)
- **THEN** le panneau est réaffiché avec le message d'erreur et les valeurs saisies

### Requirement: Le modèle BonDeCommande stocke les références de facture
Le modèle `BonDeCommande` SHALL avoir un champ `numero_facture` (texte, vide par défaut, unique lorsqu'il est renseigné) et un champ `date_facturation` (date, nullable). Le champ `date_realisation` SHALL être libellé « Date d'intervention ».

#### Scenario: Champs disponibles à la création
- **WHEN** un BDC est créé
- **THEN** `numero_facture` est vide et `date_facturation` est null
