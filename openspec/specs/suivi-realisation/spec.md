### Requirement: Le CDT peut valider la réalisation d'un BDC
Le système SHALL permettre au CDT de marquer un BDC EN_COURS comme réalisé via `valider_realisation(bdc, utilisateur)`. Le statut SHALL passer à A_FACTURER. La `date_realisation` SHALL être remplie automatiquement avec la date du jour. L'action VALIDATION SHALL être tracée dans l'historique.

#### Scenario: Validation réalisation réussie
- **WHEN** le CDT appelle `valider_realisation()` sur un BDC EN_COURS
- **THEN** le statut passe à A_FACTURER, `date_realisation` est remplie avec la date du jour, une action VALIDATION est tracée dans l'historique

#### Scenario: Validation refuse si pas EN_COURS
- **WHEN** le CDT appelle `valider_realisation()` sur un BDC qui n'est pas EN_COURS
- **THEN** une erreur `TransitionInvalide` est levée

#### Scenario: Historique de validation
- **WHEN** la validation réussit
- **THEN** l'historique contient une entrée VALIDATION avec les détails (date_realisation)

### Requirement: Le CDT peut passer un BDC en facturation
Le système SHALL permettre au CDT de passer un BDC A_FACTURER au statut FACTURE via `valider_facturation(bdc, utilisateur)`. L'action FACTURATION SHALL être tracée dans l'historique.

#### Scenario: Passage en facturation réussi
- **WHEN** le CDT appelle `valider_facturation()` sur un BDC A_FACTURER
- **THEN** le statut passe à FACTURE, une action FACTURATION est tracée dans l'historique

#### Scenario: Facturation refuse si pas A_FACTURER
- **WHEN** le CDT appelle `valider_facturation()` sur un BDC qui n'est pas A_FACTURER
- **THEN** une erreur `TransitionInvalide` est levée

### Requirement: Le CDT peut annuler une validation (retour EN_COURS)
Le système SHALL permettre au CDT de ramener un BDC A_FACTURER en EN_COURS via la transition existante. La `date_realisation` SHALL être réinitialisée à null.

#### Scenario: Retour en EN_COURS réussi
- **WHEN** le CDT utilise `changer_statut()` pour passer un BDC de A_FACTURER à EN_COURS
- **THEN** le statut revient à EN_COURS, `date_realisation` est remise à null

### Requirement: Le modèle BonDeCommande a un champ date_realisation
Le modèle `BonDeCommande` SHALL avoir un champ `date_realisation` (DateField, nullable, blank) pour stocker la date à laquelle les travaux ont été déclarés terminés.

#### Scenario: Champ date_realisation disponible
- **WHEN** un BDC est créé
- **THEN** le champ `date_realisation` est disponible, initialement null

### Requirement: La vue valider_realisation est accessible au CDT
La vue `valider_realisation_bdc` SHALL être une vue POST-only accessible uniquement au groupe CDT. Elle SHALL appeler `valider_realisation()` du service et rediriger vers la fiche détail.

#### Scenario: POST valide par un CDT
- **WHEN** un CDT POST sur `/<pk>/valider/`
- **THEN** la réalisation est validée et l'utilisateur est redirigé vers la fiche détail avec un message de succès

#### Scenario: Accès secrétaire refusé
- **WHEN** une secrétaire POST sur `/<pk>/valider/`
- **THEN** l'accès est refusé (403)

#### Scenario: GET redirige
- **WHEN** un GET est envoyé sur `/<pk>/valider/`
- **THEN** la requête est redirigée vers la fiche détail

### Requirement: La vue valider_facturation est accessible au CDT
La vue `valider_facturation_bdc` SHALL être une vue POST-only accessible uniquement au groupe CDT. Elle SHALL appeler `valider_facturation()` du service et rediriger vers la fiche détail.

#### Scenario: POST valide par un CDT
- **WHEN** un CDT POST sur `/<pk>/facturer/`
- **THEN** le BDC passe en FACTURE et l'utilisateur est redirigé vers la fiche détail avec un message de succès

#### Scenario: Accès secrétaire refusé
- **WHEN** une secrétaire POST sur `/<pk>/facturer/`
- **THEN** l'accès est refusé (403)
