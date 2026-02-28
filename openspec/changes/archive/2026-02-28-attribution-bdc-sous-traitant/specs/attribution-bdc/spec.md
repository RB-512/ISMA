## ADDED Requirements

### Requirement: Le CDT peut attribuer un BDC à un sous-traitant
Le système SHALL permettre au CDT d'attribuer un BDC en statut `A_FAIRE` à un sous-traitant actif. L'attribution SHALL enregistrer le sous-traitant, le pourcentage ST, et le montant ST calculé. Le BDC SHALL passer automatiquement en statut `EN_COURS` après attribution.

#### Scenario: Attribution réussie d'un BDC à un ST
- **WHEN** le CDT soumet le formulaire d'attribution avec un ST actif et un pourcentage de 60%
- **THEN** le BDC est attribué au ST, `pourcentage_st` vaut 60, `montant_st` vaut `montant_ht * 60 / 100`, le statut passe à `EN_COURS`, et une action `ATTRIBUTION` est tracée dans l'historique

#### Scenario: Calcul du montant ST
- **WHEN** le BDC a `montant_ht = 167.85` et le CDT saisit `pourcentage_st = 60`
- **THEN** `montant_st` vaut `Decimal("100.71")` (arrondi à 2 décimales)

#### Scenario: Attribution sans montant HT
- **WHEN** le BDC a `montant_ht = None` et le CDT attribue avec un pourcentage
- **THEN** l'attribution réussit, `montant_st` reste `None`, le pourcentage est enregistré

#### Scenario: Attribution refusée si statut incorrect
- **WHEN** le CDT tente d'attribuer un BDC en statut `A_TRAITER`
- **THEN** un message d'erreur est affiché et le BDC reste inchangé

#### Scenario: Attribution refusée si ST inactif
- **WHEN** le CDT sélectionne un ST avec `actif=False`
- **THEN** le formulaire affiche une erreur de validation

### Requirement: La page d'attribution affiche un formulaire de sélection ST
La vue `attribuer_bdc` SHALL afficher un formulaire avec la sélection du ST (uniquement les ST actifs), le champ pourcentage ST, et un résumé du BDC. La vue SHALL être accessible uniquement au groupe CDT.

#### Scenario: Affichage du formulaire d'attribution
- **WHEN** le CDT accède à `/<pk>/attribuer/` pour un BDC en statut `A_FAIRE`
- **THEN** le formulaire affiche la liste des ST actifs, le champ pourcentage, et un résumé du BDC (numéro, adresse, objet)

#### Scenario: Accès CDT uniquement
- **WHEN** un utilisateur du groupe Secretaire tente d'accéder à `/<pk>/attribuer/`
- **THEN** l'accès est refusé (403)

#### Scenario: Accès refusé si statut incorrect
- **WHEN** le CDT accède à `/<pk>/attribuer/` pour un BDC en statut `EN_COURS`
- **THEN** un message d'erreur est affiché et le CDT est redirigé vers la fiche détail

### Requirement: Le CDT peut réattribuer un BDC en cours à un autre ST
La réattribution SHALL être possible uniquement pour les BDC en statut `EN_COURS`. La réattribution SHALL tracer l'ancien et le nouveau ST dans l'historique avec l'action `REATTRIBUTION`. Le statut reste `EN_COURS`.

#### Scenario: Réattribution réussie
- **WHEN** le CDT réattribue un BDC en statut `EN_COURS` de ST-A vers ST-B avec 70%
- **THEN** `sous_traitant` devient ST-B, `pourcentage_st` vaut 70, `montant_st` est recalculé, une action `REATTRIBUTION` est tracée avec l'ancien ST dans les détails

#### Scenario: Réattribution refusée si statut incorrect
- **WHEN** le CDT tente de réattribuer un BDC en statut `A_FACTURER`
- **THEN** un message d'erreur est affiché et le BDC reste inchangé

#### Scenario: Historique de réattribution
- **WHEN** une réattribution est effectuée
- **THEN** l'historique contient les détails `{"ancien_st": "Dupont Peinture", "nouveau_st": "Martin Peinture", "pourcentage": 70}`

### Requirement: La fonction attribuer_st encapsule la logique métier
`attribuer_st(bdc, sous_traitant, pourcentage, utilisateur)` SHALL valider le statut (`A_FAIRE`), assigner le ST et le pourcentage, calculer le montant ST, changer le statut en `EN_COURS`, et tracer l'historique. Elle SHALL lever `TransitionInvalide` si le statut n'est pas `A_FAIRE`.

#### Scenario: Appel avec BDC en A_FAIRE
- **WHEN** `attribuer_st()` est appelé avec un BDC en `A_FAIRE`
- **THEN** le BDC est attribué, le statut passe en `EN_COURS`, l'historique est tracé

#### Scenario: Appel avec BDC en mauvais statut
- **WHEN** `attribuer_st()` est appelé avec un BDC en `A_TRAITER`
- **THEN** `TransitionInvalide` est levée

### Requirement: La fonction reattribuer_st encapsule la logique de réattribution
`reattribuer_st(bdc, nouveau_st, pourcentage, utilisateur)` SHALL valider que le statut est `EN_COURS`, sauvegarder l'ancien ST, assigner le nouveau, recalculer le montant, et tracer l'historique avec action `REATTRIBUTION`.

#### Scenario: Appel avec BDC en EN_COURS
- **WHEN** `reattribuer_st()` est appelé avec un BDC en `EN_COURS`
- **THEN** le ST est changé, le montant recalculé, l'historique trace l'ancien et le nouveau ST

#### Scenario: Appel avec BDC en mauvais statut
- **WHEN** `reattribuer_st()` est appelé avec un BDC en `A_FAIRE`
- **THEN** `TransitionInvalide` est levée

### Requirement: La notification SMS est préparée en stub
`notifier_st_attribution(bdc)` SHALL construire un message SMS contenant l'adresse, l'occupation (vacant/occupé), la modalité d'accès, l'objet travaux, et le délai. Le message ne SHALL JAMAIS contenir de prix. En V1, le message est loggé (pas d'envoi réel).

#### Scenario: Construction du message SMS
- **WHEN** `notifier_st_attribution()` est appelé pour un BDC attribué
- **THEN** le message contient l'adresse, l'occupation, et l'objet travaux, mais PAS les montants

#### Scenario: Logging du SMS en V1
- **WHEN** `notifier_st_attribution()` est appelé
- **THEN** le message est loggé via `logger.info` avec le numéro de téléphone du ST

### Requirement: Les routes URL sont configurées pour l'attribution
Le fichier `urls.py` SHALL contenir les routes `<int:pk>/attribuer/` et `<int:pk>/reattribuer/`.

#### Scenario: Route attribuer
- **WHEN** un GET ou POST est envoyé sur `/bdc/42/attribuer/`
- **THEN** la vue `attribuer_bdc` est appelée avec `pk=42`

#### Scenario: Route reattribuer
- **WHEN** un GET ou POST est envoyé sur `/bdc/42/reattribuer/`
- **THEN** la vue `reattribuer_bdc` est appelée avec `pk=42`

### Requirement: Le template liste des sous-traitants affiche les ST actifs
Le template `sous_traitants/list.html` SHALL afficher la liste des sous-traitants actifs avec nom, téléphone et email.

#### Scenario: Affichage de la liste ST
- **WHEN** un utilisateur authentifié accède à la page liste ST
- **THEN** les ST actifs sont affichés avec nom, téléphone et email
