## ADDED Requirements

### Requirement: Validation et facturation atomiques
Les fonctions `valider_realisation` et `valider_facturation` DOIVENT s'executer dans une transaction atomique.

#### Scenario: Crash apres save mais avant historique
- **WHEN** une erreur survient apres `bdc.save()` mais avant `HistoriqueAction.objects.create()`
- **THEN** la base de donnees est restauree (statut inchange, pas d'historique orphelin)
