## MODIFIED Requirements

### Requirement: La fonction attribuer_st encapsule la logique métier
`attribuer_st(bdc, sous_traitant, pourcentage, utilisateur)` SHALL valider le statut (`A_FAIRE`), assigner le ST et le pourcentage, calculer le montant ST, changer le statut en `EN_COURS`, tracer l'historique, et déclencher les notifications SMS et email au sous-traitant. Elle SHALL lever `TransitionInvalide` si le statut n'est pas `A_FAIRE`. Quand `pourcentage` est `None` (ex : mode forfait sans lignes), `montant_st` SHALL rester `None` sans déclencher d'erreur.

#### Scenario: Appel avec BDC en A_FAIRE
- **WHEN** `attribuer_st()` est appelé avec un BDC en `A_FAIRE`
- **THEN** le BDC est attribué, le statut passe en `EN_COURS`, l'historique est tracé, et les notifications SMS/email sont envoyées

#### Scenario: Attribution en mode forfait sans lignes
- **WHEN** `attribuer_st()` est appelé avec `mode="forfait"` et `lignes_forfait=[]` et `pourcentage=None`
- **THEN** l'attribution réussit sans erreur 500, `montant_st` vaut `None`, le BDC passe en `EN_COURS`

#### Scenario: Attribution en mode pourcentage avec montant HT
- **WHEN** `attribuer_st()` est appelé avec `pourcentage=60` et `bdc.montant_ht=100`
- **THEN** `montant_st` vaut `Decimal("60.00")`

#### Scenario: Attribution avec pourcentage None et montant HT présent
- **WHEN** `_calculer_montant_st(bdc, None)` est appelé avec `bdc.montant_ht` non null
- **THEN** la fonction retourne `None` sans lever d'exception

## ADDED Requirements

### Requirement: La vue attribution_partial transmet joindre_bdc au service
La vue `attribution_partial` SHALL lire le paramètre `joindre_bdc` depuis le POST (valeur `"on"` = True) et le transmettre à `attribuer_st` et `reattribuer_st`, de manière identique à `attribution_split`.

#### Scenario: joindre_bdc transmis dans attribution_partial
- **WHEN** le formulaire dans `attribution_partial` est soumis avec `joindre_bdc=on`
- **THEN** `attribuer_st` est appelé avec `joindre_bdc=True` et le PDF est joint à l'email

#### Scenario: joindre_bdc absent dans attribution_partial
- **WHEN** le formulaire dans `attribution_partial` est soumis sans `joindre_bdc`
- **THEN** `attribuer_st` est appelé avec `joindre_bdc=False` et aucun PDF n'est joint
