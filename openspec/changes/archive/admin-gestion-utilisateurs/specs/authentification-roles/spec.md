## MODIFIED Requirements

### Requirement: Authentification par login/mot de passe

Le systeme SHALL fournir une authentification par email/mot de passe via django-allauth. Les comptes sont crees par un administrateur (pas d'inscription publique). A la creation d'un compte, le systeme SHALL creer un enregistrement `EmailAddress` allauth avec `verified=True` et `primary=True` pour garantir le login par email.

#### Scenario: Login reussi
- **WHEN** un utilisateur saisit un email et mot de passe valides sur la page de login
- **THEN** il est authentifie et redirige vers la page d'accueil

#### Scenario: Login echoue
- **WHEN** un utilisateur saisit un mot de passe incorrect
- **THEN** un message d'erreur est affiche et l'utilisateur reste sur la page de login

#### Scenario: Acces non authentifie redirige vers login
- **WHEN** un utilisateur non authentifie tente d'acceder a une page protegee
- **THEN** il est redirige vers la page de login

#### Scenario: Compte desactive ne peut pas se connecter
- **WHEN** un utilisateur avec `is_active=False` tente de se connecter avec des identifiants valides
- **THEN** le login est refuse avec un message d'erreur
