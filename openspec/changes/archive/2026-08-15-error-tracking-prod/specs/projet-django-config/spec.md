## ADDED Requirements

### Requirement: La configuration prod inclut ADMINS et LOGGING
Le fichier `prod.py` SHALL définir `ADMINS` avec l'adresse `bybondecommande@gmail.com` et un bloc `LOGGING` configurant un handler fichier rotatif sur `/data/logs/django.log` et un `AdminEmailHandler` pour les erreurs 500.

#### Scenario: ADMINS défini en prod
- **WHEN** DJANGO_SETTINGS_MODULE vaut `config.settings.prod` ou `config.settings.prod_nossl`
- **THEN** `settings.ADMINS` contient au moins une entrée avec l'email `bybondecommande@gmail.com`

#### Scenario: LOGGING configure le fichier et l'email
- **WHEN** DJANGO_SETTINGS_MODULE vaut `config.settings.prod`
- **THEN** `settings.LOGGING` définit un `RotatingFileHandler` sur `/data/logs/django.log` et un `AdminEmailHandler` sur le logger `django`
