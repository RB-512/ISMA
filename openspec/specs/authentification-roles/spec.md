## ADDED Requirements

### Requirement: Authentification par login/mot de passe

Le systeme SHALL fournir une authentification par email/mot de passe via django-allauth. Les comptes sont crees par un administrateur (pas d'inscription publique).

#### Scenario: Login reussi
- **WHEN** un utilisateur saisit un email et mot de passe valides sur la page de login
- **THEN** il est authentifie et redirige vers la page d'accueil

#### Scenario: Login echoue
- **WHEN** un utilisateur saisit un mot de passe incorrect
- **THEN** un message d'erreur est affiche et l'utilisateur reste sur la page de login

#### Scenario: Acces non authentifie redirige vers login
- **WHEN** un utilisateur non authentifie tente d'acceder a une page protegee
- **THEN** il est redirige vers la page de login

### Requirement: Logout

Le systeme SHALL permettre a un utilisateur authentifie de se deconnecter.

#### Scenario: Logout reussi
- **WHEN** un utilisateur clique sur le bouton de deconnexion
- **THEN** sa session est invalidee et il est redirige vers la page de login

### Requirement: Groupe Secretaire avec permissions restreintes

Le systeme SHALL definir un groupe "Secretaire" avec les permissions : creer un BDC, modifier un BDC, voir le tableau de bord, voir les prix, transition A_TRAITER <-> A_FAIRE.

#### Scenario: La secretaire ne peut pas attribuer
- **WHEN** un utilisateur du groupe Secretaire tente d'acceder a la fonction d'attribution
- **THEN** l'acces est refuse (403 Forbidden)

### Requirement: Groupe CDT avec permissions completes

Le systeme SHALL definir un groupe "CDT" avec toutes les permissions du groupe Secretaire plus : attribuer, reattribuer, valider la realisation, gerer la facturation, toutes les transitions de statut.

#### Scenario: Le CDT peut attribuer un BDC
- **WHEN** un utilisateur du groupe CDT accede a la fonction d'attribution
- **THEN** l'acces est autorise

### Requirement: Decorateur et mixin de controle d'acces par groupe

Le systeme SHALL fournir un decorateur `@group_required("NomGroupe")` pour les vues fonctions et un mixin `GroupRequiredMixin` pour les vues classes.

#### Scenario: Vue protegee par decorateur
- **WHEN** une vue est decoree avec `@group_required("CDT")` et un utilisateur Secretaire y accede
- **THEN** l'acces est refuse avec un code HTTP 403

#### Scenario: Vue protegee par mixin
- **WHEN** une vue classe utilise `GroupRequiredMixin` avec `group_required = "CDT"` et un CDT y accede
- **THEN** l'acces est autorise

### Requirement: Creation des groupes via migration de donnees

Le systeme SHALL creer les groupes "Secretaire" et "CDT" via une migration de donnees Django (data migration), garantissant leur existence sur tout nouvel environnement.

#### Scenario: Les groupes existent apres migration
- **WHEN** les migrations sont appliquees sur une base vierge
- **THEN** les groupes "Secretaire" et "CDT" existent dans la table auth_group
