## 1. Scaffolding projet et configuration

- [x] 1.1 Creer le repertoire `bdc-peinture/` avec `manage.py` et le package `config/` (settings, urls, wsgi)
- [x] 1.2 Creer `pyproject.toml` avec les dependances (Django 5.x, django-allauth, django-filter, pdfplumber, PyMuPDF, psycopg[binary], gunicorn) et les dev deps (pytest, pytest-django, ruff)
- [x] 1.3 Creer `config/settings/base.py` avec les settings communs (INSTALLED_APPS, MIDDLEWARE, AUTH, MEDIA, STATIC, TEMPLATES)
- [x] 1.4 Creer `config/settings/dev.py` (DEBUG=True, DATABASE PostgreSQL Docker, ALLOWED_HOSTS localhost)
- [x] 1.5 Creer `config/settings/prod.py` (DEBUG=False, SECURE_SSL_REDIRECT, SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE)
- [x] 1.6 Creer `config/urls.py` avec les routes principales (admin, accounts, bdc)
- [x] 1.7 Creer `.env.example` avec les variables documentees (SECRET_KEY, DATABASE_URL, DEBUG, ALLOWED_HOSTS)
- [x] 1.8 Configurer Ruff dans `pyproject.toml` (linting + formatage)
- [x] 1.9 Configurer pytest dans `pyproject.toml` (DJANGO_SETTINGS_MODULE, pythonpath)

## 2. Docker Compose

- [x] 2.1 Creer `docker-compose.yml` avec le service PostgreSQL 16 (port 5432, volume persistant, credentials via .env)
- [x] 2.2 Creer `Dockerfile` pour l'application Django (Python 3.12, uv, gunicorn)

## 3. Structure des apps Django

- [x] 3.1 Creer l'app `apps/accounts/` avec __init__.py, models.py, views.py, forms.py, urls.py, decorators.py
- [x] 3.2 Creer l'app `apps/bdc/` avec __init__.py, models.py, views.py, forms.py, filters.py, services.py, urls.py, admin.py
- [x] 3.3 Creer l'app `apps/pdf_extraction/` avec __init__.py, base.py, gdh_parser.py, erilia_parser.py, detector.py (fichiers vides/squelettes)
- [x] 3.4 Creer l'app `apps/sous_traitants/` avec __init__.py, models.py, views.py, urls.py, admin.py
- [x] 3.5 Creer l'app `apps/notifications/` avec __init__.py, sms.py, email.py (squelettes)

## 4. Modeles de donnees

- [x] 4.1 Implementer le modele `Bailleur` dans `apps/bdc/models.py` (nom, code, unicite)
- [x] 4.2 Implementer le modele `SousTraitant` dans `apps/sous_traitants/models.py` (nom, telephone, email, actif)
- [x] 4.3 Implementer le modele `BonDeCommande` dans `apps/bdc/models.py` avec tous les champs du PRD (identification, localisation, travaux, contacts, montants, infos manuelles, workflow, fichiers, meta)
- [x] 4.4 Implementer les choix de statut (A_TRAITER, A_FAIRE, EN_COURS, A_FACTURER, FACTURE) et le statut par defaut A_TRAITER
- [x] 4.5 Implementer le modele `LignePrestation` dans `apps/bdc/models.py` (FK BDC, designation, quantite, unite, prix_unitaire, montant, ordre, cascade delete)
- [x] 4.6 Implementer le modele `HistoriqueAction` dans `apps/bdc/models.py` (FK BDC, FK User, action choices, details JSONField, created_at)
- [x] 4.7 Configurer le upload path du FileField pdf_original vers `bdc/<annee>/<mois>/`
- [x] 4.8 Generer et appliquer les migrations initiales

## 5. Workflow de statuts

- [x] 5.1 Implementer le dictionnaire TRANSITIONS dans `apps/bdc/services.py`
- [x] 5.2 Implementer la fonction `changer_statut(bdc, nouveau_statut, utilisateur)` qui valide la transition et cree l'entree HistoriqueAction
- [x] 5.3 Ecrire les tests du workflow dans `tests/test_bdc/test_workflow.py` (transitions valides, invalides, etat terminal FACTURE)

## 6. Authentification et roles

- [x] 6.1 Configurer django-allauth dans settings (AUTHENTICATION_BACKENDS, ACCOUNT_* settings, login/logout URLs)
- [x] 6.2 Creer la data migration pour les groupes "Secretaire" et "CDT"
- [x] 6.3 Implementer le decorateur `@group_required` dans `apps/accounts/decorators.py`
- [x] 6.4 Implementer le mixin `GroupRequiredMixin` dans `apps/accounts/decorators.py`
- [x] 6.5 Creer la vue de login et la vue de logout dans `apps/accounts/views.py`
- [x] 6.6 Configurer les URLs d'authentification dans `apps/accounts/urls.py`
- [x] 6.7 Ecrire les tests d'authentification dans `tests/test_accounts/` (login, logout, acces refuse, group_required)

## 7. Templates et frontend

- [x] 7.1 Creer `tailwind.config.js` configurant le scan des templates Django
- [x] 7.2 Creer `templates/base.html` avec layout (nav, bloc content, bloc title), chargement HTMX 2.x, Alpine.js 3.x, lien CSS Tailwind
- [x] 7.3 Creer `templates/accounts/login.html` avec formulaire de connexion style Tailwind
- [x] 7.4 Generer `static/css/output.css` avec le CLI Tailwind standalone
- [x] 7.5 Creer le repertoire `templates/bdc/partials/` (vide, pret pour les fragments HTMX)

## 8. Tests de base et verification

- [x] 8.1 Creer `tests/conftest.py` avec fixtures pytest (utilisateur secretaire, utilisateur CDT, bailleur GDH, bailleur ERILIA)
- [x] 8.2 Ecrire les tests des modeles dans `tests/test_bdc/test_models.py` (creation BDC, unicite numero, lignes prestation, historique)
- [x] 8.3 Verifier que `uv run ruff check .` passe sans erreur
- [x] 8.4 Verifier que `uv run pytest` passe avec tous les tests au vert
