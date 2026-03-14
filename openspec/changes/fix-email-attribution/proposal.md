## Why

Les emails de notification aux sous-traitants lors de l'attribution d'un BDC ne sont pas envoyés en production. Le code est implémenté et fonctionnel (`apps/notifications/email.py`, `apps/bdc/services.py`) mais la variable d'environnement `EMAIL_HOST_PASSWORD` est vide dans le `.env` du VPS. De plus, Gmail requiert un "App Password" (mot de passe d'application) et non le mot de passe du compte, et les erreurs SMTP sont silencieusement avalées par le try/except dans `_notifier_st_si_possible`.

## What Changes

- Configurer `EMAIL_HOST_PASSWORD` avec un App Password Gmail sur le VPS
- Ajouter un log visible (warning) quand l'envoi échoue, pour diagnostiquer en prod
- Vérifier que `envoyer_email_attribution` fonctionne de bout en bout via un test manuel

## Capabilities

### New Capabilities

_(aucune)_

### Modified Capabilities

_(aucune — pas de changement de spec, uniquement configuration et diagnostic)_

## Impact

- Fichier `.env` sur le VPS (`EMAIL_HOST_PASSWORD`)
- `apps/bdc/services.py` : les exceptions sont déjà loggées, mais les logs ne sont pas consultés → ajouter un message flash visible à l'utilisateur si l'email échoue
- `apps/bdc/notifications.py` : la fonction stub `notifier_st_attribution` n'est plus utilisée (le vrai envoi passe par `services._notifier_st_si_possible` → `notifications.email.envoyer_email_attribution`)
