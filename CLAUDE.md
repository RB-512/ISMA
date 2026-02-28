# BDC Peinture

Application Django MVP pour la gestion des bons de commande d'une entreprise de peinture (bailleurs sociaux : GDH, ERILIA...).
Upload PDF du bon de commande bailleur -> extraction automatique des champs et lignes de prestation -> formulaire de creation -> workflow de suivi.
Utilisateurs : Secretaire (saisie, upload), Chef de Travaux / CDT (validation, suivi chantier).

## Commandes essentielles

```bash
# Depuis bdc-peinture/
uv sync                              # Installer les dependances
uv run manage.py runserver            # Serveur de dev
uv run pytest                        # Lancer les tests
uv run pytest -v --tb=short          # Tests verbose
uv run ruff check .                  # Linting
uv run ruff check --fix .            # Auto-fix linting
uv run ruff format .                 # Formattage
uv run manage.py makemigrations      # Creer migrations
uv run manage.py migrate             # Appliquer migrations
docker compose up db -d              # Demarrer PostgreSQL
```

## Stack technique

- **Backend** : Django 5.1, Python 3.12+, PostgreSQL 16
- **Frontend** : Django Templates + HTMX 2.x + Alpine.js 3.x + Tailwind CSS
- **PDF** : pdfplumber (primaire), PyMuPDF (fallback)
- **Gestionnaire** : uv (pas pip)
- **Tests** : pytest + pytest-django + factory-boy
- **Linting** : Ruff (line-length=119, rules: E, W, F, I, N, UP, B, C4, DJ)

## Structure projet

```
bdc-peinture/
  config/settings/          # base.py, dev.py, dev_sqlite.py, prod.py, test.py
  apps/
    bdc/                    # Modeles BDC, vues, services, workflow
    pdf_extraction/         # Parsers PDF (GDH, ERILIA), detecteur auto
    accounts/               # Auth, groupes, decorateur @group_required
    sous_traitants/         # Gestion sous-traitants
    notifications/          # SMS (Twilio/OVH), Email
  templates/                # Templates Django avec Tailwind
    bdc/partials/           # Fragments HTMX
  tests/                    # Organises par app (test_bdc/, test_pdf_extraction/, test_accounts/)
```

## Patterns architecturaux

- **Service layer** : logique metier dans `services.py`, pas dans les vues
- **Parsers PDF** : heriter de `PDFParser` (base.py), un parser par bailleur
- **RBAC** : utiliser `@group_required('Secretaire')` ou `@group_required('CDT')`
- **UI dynamique** : HTMX pour les interactions, pas de JS framework lourd
- **Partials** : fragments HTMX dans `templates/bdc/partials/`

## Conventions de code

- Python 3.12+, pas de type hints sauf interfaces publiques
- Line length : 119 caracteres
- Imports tries par Ruff (isort integre)
- Noms en francais pour le metier (BonDeCommande, LignePrestation, SousTraitant)
- Noms techniques en anglais (views, forms, services, filters)

## Workflow metier (statuts BDC)

```
A_TRAITER -> A_FAIRE -> EN_COURS -> A_FACTURER -> FACTURE
```

Transitions definies dans `apps/bdc/services.py` (TRANSITIONS_VALIDES).

## OpenSpec

- Specs : `openspec/specs/` (une par feature)
- Changes en cours : `openspec/changes/`
- Archive : `openspec/changes/archive/`

## Documentation de reference

- `PRD.md` : exigences fonctionnelles
- `ARCHITECTURE.md` : decisions techniques
- `docs/` : modeles PDF de reference (GDH, ERILIA)

## Context7

Utiliser Context7 pour verifier les API de : Django, HTMX, pdfplumber, Tailwind, django-allauth.
Particulierement important pour Django (evolutions frequentes) et HTMX v2.
