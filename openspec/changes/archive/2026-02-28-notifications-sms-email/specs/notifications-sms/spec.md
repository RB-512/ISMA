## ADDED Requirements

### Requirement: Le système envoie un SMS au ST lors de l'attribution d'un BDC
Le système SHALL envoyer un SMS au sous-traitant attribué contenant : adresse du logement, occupation (vacant/occupé), modalité d'accès, objet des travaux, délai d'exécution. Le SMS ne SHALL JAMAIS contenir de prix (montant HT, montant ST, pourcentage).

#### Scenario: SMS envoyé après attribution
- **WHEN** le CDT attribue un BDC à un ST ayant un numéro de téléphone
- **THEN** un SMS est envoyé au numéro du ST avec l'adresse, l'occupation, l'objet travaux et le délai

#### Scenario: SMS ne contient jamais de prix
- **WHEN** un SMS d'attribution est envoyé
- **THEN** le message ne contient ni montant HT, ni montant ST, ni pourcentage

#### Scenario: Attribution réussie même si SMS échoue
- **WHEN** l'envoi du SMS échoue (erreur réseau, credentials invalides)
- **THEN** l'attribution du BDC est quand même effectuée et l'erreur est loggée en warning

#### Scenario: Pas de SMS si ST sans téléphone
- **WHEN** le ST attribué n'a pas de numéro de téléphone
- **THEN** aucun SMS n'est envoyé et un warning est loggé

### Requirement: Le système envoie un SMS lors de la réattribution d'un BDC
Le système SHALL envoyer un SMS d'annulation à l'ancien ST et un SMS d'attribution au nouveau ST lors d'une réattribution.

#### Scenario: SMS envoyé aux deux ST lors de réattribution
- **WHEN** le CDT réattribue un BDC de ST-A vers ST-B
- **THEN** un SMS d'annulation est envoyé à ST-A et un SMS d'attribution est envoyé à ST-B

#### Scenario: Réattribution réussie même si SMS échoue
- **WHEN** l'envoi des SMS de réattribution échoue
- **THEN** la réattribution est quand même effectuée

### Requirement: Le backend SMS est configurable via settings
Le système SHALL utiliser un backend SMS configurable via `SMS_BACKEND` dans les settings Django. Le backend `LogSmsBackend` SHALL logger les SMS sans les envoyer. Le backend `OvhSmsBackend` SHALL envoyer les SMS via l'API REST OVH.

#### Scenario: Backend log en développement
- **WHEN** `SMS_BACKEND` est `"apps.notifications.backends.LogSmsBackend"`
- **THEN** les SMS sont loggés via `logger.info` sans appel réseau

#### Scenario: Backend OVH en production
- **WHEN** `SMS_BACKEND` est `"apps.notifications.backends.OvhSmsBackend"`
- **THEN** les SMS sont envoyés via l'API REST OVH (`POST /1.0/sms/{serviceName}/jobs`)

#### Scenario: Configuration OVH via variables d'environnement
- **WHEN** le backend OVH est utilisé
- **THEN** les credentials sont lus depuis `OVH_APPLICATION_KEY`, `OVH_APPLICATION_SECRET`, `OVH_CONSUMER_KEY`, `OVH_SMS_SERVICE_NAME`, `OVH_SMS_SENDER`
