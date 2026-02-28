## MODIFIED Requirements

### Requirement: La notification SMS est préparée en stub
`notifier_st_attribution(bdc)` SHALL construire un message SMS contenant l'adresse, l'occupation (vacant/occupé), la modalité d'accès, l'objet travaux, et le délai. Le message ne SHALL JAMAIS contenir de prix. Le message SHALL être envoyé via le backend SMS configuré. En cas d'échec, l'erreur est loggée sans bloquer l'attribution.

#### Scenario: Construction du message SMS
- **WHEN** `notifier_st_attribution()` est appelé pour un BDC attribué
- **THEN** le message contient l'adresse, l'occupation, et l'objet travaux, mais PAS les montants

#### Scenario: Envoi via backend SMS configuré
- **WHEN** `notifier_st_attribution()` est appelé
- **THEN** le SMS est envoyé via le backend configuré dans `SMS_BACKEND` et l'email avec PDF terrain est envoyé au ST

#### Scenario: Échec silencieux
- **WHEN** l'envoi SMS ou email échoue
- **THEN** l'erreur est loggée en warning et l'attribution n'est pas annulée

### Requirement: La fonction attribuer_st encapsule la logique métier
`attribuer_st(bdc, sous_traitant, pourcentage, utilisateur)` SHALL valider le statut (`A_FAIRE`), assigner le ST et le pourcentage, calculer le montant ST, changer le statut en `EN_COURS`, tracer l'historique, et déclencher les notifications SMS et email au sous-traitant. Elle SHALL lever `TransitionInvalide` si le statut n'est pas `A_FAIRE`.

#### Scenario: Appel avec BDC en A_FAIRE
- **WHEN** `attribuer_st()` est appelé avec un BDC en `A_FAIRE`
- **THEN** le BDC est attribué, le statut passe en `EN_COURS`, l'historique est tracé, et les notifications SMS/email sont envoyées

#### Scenario: Appel avec BDC en mauvais statut
- **WHEN** `attribuer_st()` est appelé avec un BDC en `A_TRAITER`
- **THEN** `TransitionInvalide` est levée

### Requirement: La fonction reattribuer_st encapsule la logique de réattribution
`reattribuer_st(bdc, nouveau_st, pourcentage, utilisateur)` SHALL valider que le statut est `EN_COURS`, sauvegarder l'ancien ST, assigner le nouveau, recalculer le montant, tracer l'historique avec action `REATTRIBUTION`, et déclencher les notifications d'annulation (ancien ST) et d'attribution (nouveau ST).

#### Scenario: Appel avec BDC en EN_COURS
- **WHEN** `reattribuer_st()` est appelé avec un BDC en `EN_COURS`
- **THEN** le ST est changé, le montant recalculé, l'historique trace l'ancien et le nouveau ST, et les notifications sont envoyées

#### Scenario: Appel avec BDC en mauvais statut
- **WHEN** `reattribuer_st()` est appelé avec un BDC en `A_FAIRE`
- **THEN** `TransitionInvalide` est levée
