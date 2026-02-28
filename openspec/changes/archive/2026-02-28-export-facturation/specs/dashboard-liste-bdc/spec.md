## MODIFIED Requirements

### Requirement: L'accès au dashboard nécessite une authentification
Le système SHALL restreindre l'accès au dashboard aux utilisateurs authentifiés (Secrétaire et CDT). Un lien "Export facturation" SHALL être affiché pour les utilisateurs CDT, pointant vers `/bdc/export/`.

#### Scenario: Utilisateur non authentifié
- **WHEN** un utilisateur non authentifié accède à `/bdc/`
- **THEN** il est redirigé vers la page de login

#### Scenario: Utilisateur authentifié (Secrétaire ou CDT)
- **WHEN** un utilisateur authentifié accède à `/bdc/`
- **THEN** le dashboard est affiché normalement

#### Scenario: Lien Export facturation pour CDT
- **WHEN** un utilisateur CDT accède à `/bdc/`
- **THEN** un lien "Export facturation" est affiché dans la barre d'actions

#### Scenario: Lien Export facturation masqué pour secrétaire
- **WHEN** une secrétaire accède à `/bdc/`
- **THEN** le lien "Export facturation" n'est pas affiché
