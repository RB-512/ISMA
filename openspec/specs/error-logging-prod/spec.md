## ADDED Requirements

### Requirement: Les erreurs 500 sont notifiées par email
Le système SHALL envoyer un email à `bybondecommande@gmail.com` à chaque erreur 500 non catchée en production. L'email SHALL contenir le stack trace complet, l'URL de la requête, et l'utilisateur concerné. L'envoi SHALL utiliser le backend SMTP déjà configuré.

#### Scenario: Erreur 500 déclenche un email
- **WHEN** une exception non gérée se produit dans une vue Django en production
- **THEN** un email est envoyé à `bybondecommande@gmail.com` avec le traceback complet dans les secondes qui suivent

#### Scenario: Email non envoyé en dev
- **WHEN** DJANGO_SETTINGS_MODULE vaut `config.settings.dev`
- **THEN** aucun email d'erreur n'est envoyé (configuration LOGGING absente en dev)

### Requirement: Les erreurs sont persistées dans un fichier de log rotatif
Le système SHALL écrire tous les événements de niveau ERROR et supérieur dans `/data/logs/django.log`. Le fichier SHALL être rotatif (max 10 Mo, 5 fichiers de backup) pour éviter la saturation du disque. Le fichier SHALL persister entre les redémarrages du conteneur Docker via un volume dédié.

#### Scenario: Fichier log créé au démarrage
- **WHEN** le conteneur Docker web démarre en production
- **THEN** le fichier `/data/logs/django.log` est créé et accessible

#### Scenario: Rotation des logs
- **WHEN** le fichier `django.log` atteint 10 Mo
- **THEN** il est renommé `django.log.1` et un nouveau fichier `django.log` est créé ; les fichiers au-delà de `.5` sont supprimés

#### Scenario: Persistance entre redémarrages
- **WHEN** le conteneur web est redémarré via `docker compose restart web`
- **THEN** le fichier `/data/logs/django.log` contient toujours les entrées précédentes
