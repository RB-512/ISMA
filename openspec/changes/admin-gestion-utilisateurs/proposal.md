## Why

La page "Gestion des accès" existante (CDT uniquement) présente des lacunes critiques : pas de champ email à la création (alors que le login allauth utilise l'email), pas de réinitialisation de mot de passe par l'admin, pas de réactivation des comptes désactivés, et pas de modification des informations utilisateur après création. L'administrateur (CDT) ne peut pas gérer efficacement les identifiants de son équipe.

## What Changes

- Ajouter le champ **email** (obligatoire) au formulaire de création d'utilisateur, avec création automatique de l'`EmailAddress` allauth associée (vérifiée)
- Permettre la **modification** des informations d'un utilisateur existant (nom, prénom, email, rôle)
- Permettre la **réinitialisation du mot de passe** par l'admin (génération d'un nouveau mot de passe temporaire)
- Permettre la **réactivation** d'un compte désactivé
- Améliorer l'UX de la page de gestion : feedback visuel, actions inline HTMX

## Capabilities

### New Capabilities

- `admin-utilisateurs`: Gestion complète des utilisateurs par le CDT — CRUD utilisateurs, reset mot de passe, activation/désactivation, modification rôle et profil

### Modified Capabilities

- `authentification-roles`: Ajout du champ email obligatoire à la création, EmailAddress allauth synchronisée automatiquement

## Impact

- `apps/accounts/forms.py` : ajout champ email, nouveau formulaire de modification
- `apps/accounts/views.py` : nouvelles vues modifier, réactiver, reset password
- `apps/accounts/urls.py` (namespace `gestion`) : nouvelles routes
- `templates/accounts/utilisateurs.html` : refonte pour supporter les actions inline
- Dépendance existante : `django-allauth` (EmailAddress model)
