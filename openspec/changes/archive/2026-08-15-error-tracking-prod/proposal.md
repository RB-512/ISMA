## Why

En production, les erreurs 500 disparaissent silencieusement dans Docker stderr : aucune notification, aucun historique. Le conducteur de travaux rapporte des erreurs 500 lors de l'attribution, mais il est impossible de les diagnostiquer à distance sans avoir mis en place un système de capture.

## What Changes

- Ajout d'une configuration `LOGGING` dans `prod.py` : fichier rotatif `/data/logs/django.log` + envoi email immédiat sur erreur 500 via `AdminEmailHandler`
- Ajout de `ADMINS` pointant vers `bybondecommande@gmail.com` (utilise le SMTP déjà configuré)
- Ajout d'un volume Docker `log_data` monté sur `/data/logs/` dans `docker-compose.prod.yml` pour persister les logs entre redémarrages

## Capabilities

### New Capabilities

- `error-logging-prod` : Capture et persistance des erreurs 500 en production avec notification email et fichier de log rotatif

### Modified Capabilities

- `projet-django-config` : Ajout de la configuration LOGGING et ADMINS dans les settings de production

## Impact

- `bdc-peinture/config/settings/prod.py` : ajout LOGGING + ADMINS
- `bdc-peinture/docker-compose.prod.yml` : ajout volume `log_data`
- Aucun impact sur le code applicatif, aucune migration
- Dépend du SMTP déjà configuré en prod (EMAIL_HOST, EMAIL_HOST_USER, etc.)
