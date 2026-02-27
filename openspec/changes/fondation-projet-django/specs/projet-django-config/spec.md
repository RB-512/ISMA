## ADDED Requirements

### Requirement: Projet Django initialise avec structure multi-apps

Le systeme SHALL fournir un projet Django 5.x fonctionnel avec la structure d'apps definie dans ARCHITECTURE.md : `config/` (settings), `apps/accounts/`, `apps/bdc/`, `apps/pdf_extraction/`, `apps/sous_traitants/`, `apps/notifications/`.

#### Scenario: Le serveur de dev demarre sans erreur
- **WHEN** le developpeur execute `uv run manage.py runserver`
- **THEN** le serveur Django demarre sur le port 8000 sans erreur

#### Scenario: Les migrations s'appliquent sans erreur
- **WHEN** le developpeur execute `uv run manage.py migrate`
- **THEN** toutes les migrations s'appliquent avec succes sur PostgreSQL

### Requirement: Configuration settings split base/dev/prod

Le systeme SHALL utiliser un fichier `config/settings/base.py` pour les settings communs, `config/settings/dev.py` pour le developpement (DEBUG=True), et `config/settings/prod.py` pour la production (DEBUG=False, HTTPS force).

#### Scenario: Le mode dev active DEBUG
- **WHEN** DJANGO_SETTINGS_MODULE vaut `config.settings.dev`
- **THEN** DEBUG est True et la base de donnees est PostgreSQL Docker local

#### Scenario: Le mode prod desactive DEBUG
- **WHEN** DJANGO_SETTINGS_MODULE vaut `config.settings.prod`
- **THEN** DEBUG est False, SECURE_SSL_REDIRECT est True, SESSION_COOKIE_SECURE est True

### Requirement: Docker Compose pour dev local

Le systeme SHALL fournir un `docker-compose.yml` avec un service PostgreSQL 16 et les volumes necessaires pour la persistance des donnees et des fichiers media.

#### Scenario: PostgreSQL demarre via Docker Compose
- **WHEN** le developpeur execute `docker compose up db -d`
- **THEN** PostgreSQL 16 est accessible sur le port 5432 avec les credentials du fichier `.env`

#### Scenario: Le fichier .env.example documente les variables
- **WHEN** le developpeur consulte `.env.example`
- **THEN** il trouve toutes les variables necessaires : SECRET_KEY, DATABASE_URL, DEBUG, ALLOWED_HOSTS

### Requirement: Gestion des dependances via uv et pyproject.toml

Le systeme SHALL utiliser `uv` comme gestionnaire de dependances avec un `pyproject.toml` listant toutes les dependances du projet et un `uv.lock` pour la reproductibilite.

#### Scenario: Installation des dependances
- **WHEN** le developpeur execute `uv sync`
- **THEN** toutes les dependances sont installees dans un environnement virtuel

### Requirement: Configuration Ruff pour linting et formatage

Le systeme SHALL configurer Ruff dans `pyproject.toml` pour le linting et le formatage du code Python.

#### Scenario: Le linter passe sans erreur sur le code initial
- **WHEN** le developpeur execute `uv run ruff check .`
- **THEN** aucune erreur de linting n'est rapportee

### Requirement: Configuration pytest pour les tests

Le systeme SHALL configurer pytest avec pytest-django dans `pyproject.toml` et fournir un fichier `tests/conftest.py` avec les fixtures de base.

#### Scenario: Les tests passent sur le projet initial
- **WHEN** le developpeur execute `uv run pytest`
- **THEN** tous les tests passent avec succes
