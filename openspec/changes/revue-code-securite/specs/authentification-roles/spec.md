## ADDED Requirements

### Requirement: Vues workflow CDT protegees par groupe
Les vues de workflow (attribution, validation, facturation, renvoi, releves) DOIVENT etre protegees par `@group_required('CDT')` en plus de `@login_required`.

#### Scenario: Secretaire tente d'attribuer un BDC
- **WHEN** un utilisateur du groupe Secretaire accede a la vue `attribuer_bdc`
- **THEN** le systeme retourne une erreur 403 Forbidden

#### Scenario: CDT attribue un BDC
- **WHEN** un utilisateur du groupe CDT accede a la vue `attribuer_bdc`
- **THEN** le systeme autorise l'acces normalement

### Requirement: Vues gestion utilisateurs protegees par groupe
Les vues de gestion des utilisateurs (creer, modifier, supprimer, reset MDP, activer/desactiver) DOIVENT etre protegees par `@group_required('CDT')`.

#### Scenario: Secretaire tente de creer un utilisateur
- **WHEN** un utilisateur du groupe Secretaire accede a la vue `creer_utilisateur`
- **THEN** le systeme retourne une erreur 403 Forbidden

#### Scenario: Secretaire tente de reset un mot de passe
- **WHEN** un utilisateur du groupe Secretaire accede a la vue `reset_password_utilisateur`
- **THEN** le systeme retourne une erreur 403 Forbidden
