## ADDED Requirements

### Requirement: Attribution atomique
Les fonctions `attribuer_st` et `reattribuer_st` DOIVENT s'executer dans une transaction atomique. Si une etape echoue, toutes les ecritures sont annulees.

#### Scenario: Crash pendant creation des lignes forfait
- **WHEN** une erreur survient pendant la creation des `LigneForfaitAttribution` apres suppression des anciennes
- **THEN** la base de donnees est restauree a l'etat precedent (anciennes lignes conservees, statut inchange)

### Requirement: Notifications non-bloquantes
Les notifications SMS et email envoyees lors de l'attribution NE DOIVENT JAMAIS bloquer ni annuler l'attribution. Les erreurs de notification sont loggees mais n'empechent pas la transition de statut.

#### Scenario: Erreur SMTP pendant attribution
- **WHEN** l'envoi d'email echoue avec une erreur SMTP pendant `attribuer_st`
- **THEN** l'attribution est quand meme effectuee et un log d'erreur est emis
