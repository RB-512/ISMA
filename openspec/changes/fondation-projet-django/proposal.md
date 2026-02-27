## Why

Le projet BDC Peinture n'a pas encore de code. Avant de pouvoir implémenter les fonctionnalités métier (upload PDF, dashboard, attribution, facturation), il faut poser le socle technique : projet Django, base de données, authentification, structure des apps. Sans cette fondation, aucune des 7 SPEC du PRD ne peut être développée.

## What Changes

- Création du projet Django 5.x avec structure multi-apps (`accounts`, `bdc`, `pdf_extraction`, `sous_traitants`, `notifications`)
- Configuration Docker Compose pour PostgreSQL 16 + app Django
- Settings Django split (base/dev/prod) avec gestion des variables d'environnement
- Modèles de données complets : `Bailleur`, `SousTraitant`, `BonDeCommande`, `LignePrestation`, `HistoriqueAction`
- Workflow de statuts avec transitions autorisées (A_TRAITER -> A_FAIRE -> EN_COURS -> A_FACTURER -> FACTURE)
- Authentification via django-allauth + groupes de permissions (Secretaire, CDT)
- Template de base HTML avec Tailwind CSS (standalone CLI), HTMX 2.x et Alpine.js 3.x
- Configuration de l'outillage dev : uv, Ruff, pytest, pyproject.toml
- Page de login fonctionnelle

## Capabilities

### New Capabilities

- `projet-django-config`: Configuration du projet Django (settings, urls, wsgi, Docker Compose, pyproject.toml, .env)
- `modeles-donnees-bdc`: Modeles de donnees du domaine metier (BonDeCommande, LignePrestation, HistoriqueAction, Bailleur, SousTraitant) avec workflow de statuts
- `authentification-roles`: Authentification (login/logout) et systeme de roles (groupes Secretaire et CDT) avec permissions
- `base-template-ui`: Template HTML de base avec layout principal, navigation, Tailwind CSS, HTMX et Alpine.js

### Modified Capabilities

_Aucune — premier changement du projet, pas de specs existantes._

## Impact

- **Code** : Creation de l'arborescence complete du projet Django depuis zero
- **Dependencies** : Django 5.x, django-allauth, django-filter, pdfplumber, PyMuPDF, psycopg[binary], gunicorn, pytest-django, ruff
- **Infrastructure** : Docker Compose avec PostgreSQL 16, volume persistant pour /media/
- **Fichiers** : pyproject.toml, Dockerfile, docker-compose.yml, .env.example, manage.py, config/, apps/, templates/, static/, tests/
