## Why

Lors de l'attribution ou réattribution d'un BDC à un sous-traitant, celui-ci doit être notifié immédiatement par SMS et/ou email avec les informations nécessaires (adresse, travaux, accès). Actuellement, les fonctions `envoyer_sms_attribution`, `envoyer_sms_reattribution` et `envoyer_email_bdc_terrain` dans `apps/notifications/` sont des stubs (`NotImplementedError`). Le CDT doit aussi recevoir des alertes sur les BDC dont le délai d'exécution approche ou est dépassé.

## What Changes

- Implémenter l'envoi de SMS via OVH SMS API (provider principal, pas Twilio) dans `notifications/sms.py`
- Implémenter l'envoi d'email avec le BDC terrain PDF en pièce jointe via Django `send_mail` dans `notifications/email.py`
- Brancher les notifications dans le workflow d'attribution et réattribution (`services.py`)
- Ajouter un système d'alertes sur les délais d'exécution dépassés (management command + affichage dashboard)
- Configurer les settings SMS/Email avec `python-decouple` (variables d'environnement)

## Capabilities

### New Capabilities
- `notifications-sms`: Envoi de SMS aux sous-traitants lors d'attribution/réattribution via OVH SMS API
- `notifications-email`: Envoi d'email avec BDC terrain PDF en pièce jointe au sous-traitant
- `alertes-delais`: Alertes sur les BDC dont le délai d'exécution est dépassé ou proche (J-2)

### Modified Capabilities
- `attribution-bdc`: Branchement des notifications SMS/email après attribution et réattribution

## Impact

- **Code** : `apps/notifications/sms.py`, `apps/notifications/email.py`, `apps/bdc/services.py`, nouveau management command
- **Dépendances** : ajout `requests` (pour OVH SMS API REST)
- **Configuration** : nouvelles variables d'environnement `OVH_SMS_*`, `DEFAULT_FROM_EMAIL` (déjà configuré)
- **Settings** : ajout `SMS_BACKEND` pour basculer entre envoi réel et logging (dev/test)
