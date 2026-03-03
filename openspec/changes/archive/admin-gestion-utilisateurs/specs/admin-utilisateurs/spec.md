## ADDED Requirements

### Requirement: Creation d'utilisateur avec email obligatoire

Le systeme SHALL permettre au CDT de creer un utilisateur avec les champs : username, prenom, nom, email (obligatoire), mot de passe, role. A la creation, le systeme SHALL creer automatiquement un enregistrement `EmailAddress` allauth avec `verified=True` et `primary=True`.

#### Scenario: Creation reussie avec email
- **WHEN** le CDT soumet le formulaire de creation avec un email valide et unique
- **THEN** l'utilisateur est cree avec l'email renseigne, un `EmailAddress` allauth est cree (verified, primary), et le CDT voit un message de succes

#### Scenario: Creation avec email deja utilise
- **WHEN** le CDT soumet le formulaire de creation avec un email deja utilise par un autre utilisateur
- **THEN** le formulaire affiche une erreur de validation sur le champ email

#### Scenario: Creation sans email
- **WHEN** le CDT soumet le formulaire de creation sans renseigner l'email
- **THEN** le formulaire affiche une erreur indiquant que l'email est obligatoire

### Requirement: Modification du profil utilisateur

Le systeme SHALL permettre au CDT de modifier le prenom, nom, email et role d'un utilisateur existant. La modification de l'email SHALL synchroniser l'`EmailAddress` allauth associee.

#### Scenario: Modification reussie du profil
- **WHEN** le CDT modifie le prenom, nom ou role d'un utilisateur et soumet le formulaire
- **THEN** les informations sont mises a jour et un message de succes est affiche

#### Scenario: Modification de l'email avec synchronisation allauth
- **WHEN** le CDT modifie l'email d'un utilisateur
- **THEN** le champ `User.email` ET l'`EmailAddress` allauth primary sont mis a jour avec le nouvel email

#### Scenario: Modification avec email deja pris
- **WHEN** le CDT modifie l'email d'un utilisateur avec un email deja utilise par un autre utilisateur
- **THEN** le formulaire affiche une erreur de validation sur le champ email

#### Scenario: Le CDT ne peut pas modifier son propre role
- **WHEN** le CDT tente de modifier le role de son propre compte
- **THEN** le champ role est desactive ou le systeme refuse la modification

### Requirement: Reinitialisation du mot de passe par l'admin

Le systeme SHALL permettre au CDT de reinitialiser le mot de passe d'un utilisateur. Un mot de passe temporaire aleatoire est genere et affiche une seule fois au CDT.

#### Scenario: Reset mot de passe reussi
- **WHEN** le CDT clique sur "Reinitialiser le mot de passe" pour un utilisateur
- **THEN** un nouveau mot de passe aleatoire est genere, applique au compte, et affiche au CDT dans un element visible temporairement

#### Scenario: Le CDT ne peut pas reset son propre mot de passe via cette interface
- **WHEN** le CDT tente de reinitialiser son propre mot de passe
- **THEN** l'action est refusee avec un message explicatif

### Requirement: Reactivation d'un compte desactive

Le systeme SHALL permettre au CDT de reactiver un compte utilisateur precedemment desactive.

#### Scenario: Reactivation reussie
- **WHEN** le CDT clique sur "Reactiver" pour un utilisateur desactive
- **THEN** le compte est reactive (`is_active=True`) et un message de succes est affiche

#### Scenario: Bouton reactiver visible uniquement pour comptes inactifs
- **WHEN** le CDT consulte la liste des utilisateurs
- **THEN** le bouton "Reactiver" est visible uniquement pour les utilisateurs avec `is_active=False`

### Requirement: Liste des utilisateurs enrichie

Le systeme SHALL afficher la liste des utilisateurs avec leur statut (actif/inactif), email, role, et les actions disponibles (modifier, desactiver/reactiver, reset mot de passe).

#### Scenario: Affichage de la liste complete
- **WHEN** le CDT accede a la page de gestion des utilisateurs
- **THEN** il voit tous les utilisateurs avec nom, prenom, email, role, statut et actions

#### Scenario: Actions inline HTMX
- **WHEN** le CDT clique sur une action (modifier, reset)
- **THEN** l'interface affiche le formulaire ou le resultat sans rechargement complet de la page
