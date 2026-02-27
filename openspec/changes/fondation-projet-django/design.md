## Context

Le projet BDC Peinture est une application web de gestion de bons de commande pour une entreprise de peinture (~30 employes, 2-3 utilisateurs internes). L'architecture validee est un monolithe Django 5.x avec HTMX/Alpine.js/Tailwind CSS cote frontend, PostgreSQL 16 pour la base de donnees, le tout conteneurise avec Docker Compose.

Le PRD definit 7 specifications fonctionnelles (SPEC-001 a SPEC-007). Cette premiere change pose les fondations techniques sur lesquelles toutes les features seront construites.

Documents de reference :
- `PRD.md` : Exigences fonctionnelles, workflow, modele de donnees
- `ARCHITECTURE.md` : Architecture technique detaillee, structure du projet, conventions
- `TECH_STACK_REPORT.md` : Justification du choix technologique

## Goals / Non-Goals

**Goals:**
- Projet Django fonctionnel avec `manage.py runserver` operationnel
- Docker Compose avec PostgreSQL 16 pour le dev local
- Tous les modeles de donnees du PRD implementes avec migrations
- Authentification login/logout avec 2 groupes (Secretaire, CDT)
- Template de base HTML avec Tailwind CSS, HTMX, Alpine.js charges
- Page de login fonctionnelle
- Tests de base qui passent (modeles, auth)
- Outillage dev configure (uv, Ruff, pytest)

**Non-Goals:**
- Pas de vues metier (dashboard, formulaire BDC, attribution) — ce sont des changes separees
- Pas d'extraction PDF — SPEC-001 sera une change dediee
- Pas de notifications SMS/email — modules vides prepares mais pas implementes
- Pas de deploiement production (Nginx, Gunicorn, SSL) — change dediee
- Pas de CI/CD GitHub Actions
- Pas de donnees de test/fixtures metier

## Decisions

### 1. Structure multi-settings (base/dev/prod)

**Choix :** Split settings en `config/settings/base.py`, `dev.py`, `prod.py`

**Alternatives considerees :**
- Settings unique avec conditionnels `if DEBUG` — moins propre, risque d'erreur en prod
- django-environ avec un seul fichier — acceptable mais le split est plus explicite

**Raison :** Separation claire des preoccupations. `dev.py` active DEBUG, utilise SQLite ou PostgreSQL Docker. `prod.py` force HTTPS, securise les cookies. `base.py` contient tout ce qui est commun.

### 2. Gestion des dependances avec uv

**Choix :** `uv` avec `pyproject.toml` et `uv.lock`

**Alternatives considerees :**
- Poetry — plus lent, lock file plus complexe
- pip + requirements.txt — pas de lock file fiable

**Raison :** uv est le plus rapide, supporte nativement pyproject.toml, genere un lock file deterministe. Recommande par l'architecture.

### 3. Modeles nommes en francais

**Choix :** Noms de modeles et champs metier en francais (`BonDeCommande`, `sous_traitant`, `montant_ht`)

**Raison :** Les termes metier sont en francais dans le PRD. Imposer des noms anglais forcerait une traduction mentale permanente et des risques de malentendu. Le code technique reste en anglais (`created_at`, `is_active`).

### 4. Workflow via champ statut + dictionnaire de transitions

**Choix :** Champ `CharField` avec `choices` + dictionnaire Python `TRANSITIONS` dans `services.py`

**Alternatives considerees :**
- django-fsm (finite state machine) — trop de magie, overhead pour 5 statuts
- Modele `Statut` en base — complexite inutile pour des valeurs fixes

**Raison :** Simple, explicite, testable. Le dictionnaire `TRANSITIONS` valide les transitions autorisees. 5 statuts ne justifient pas une lib externe.

### 5. Tailwind CSS via CLI standalone (pas de Node.js)

**Choix :** Binaire `tailwindcss` standalone, genere `static/css/output.css`

**Alternatives considerees :**
- Tailwind via CDN — pas de purge, fichier CSS enorme en prod
- Tailwind via npm — necessite Node.js, node_modules, build step

**Raison :** Pas de dependance Node.js. Le binaire standalone genere le CSS optimise. Conforme a l'architecture.

### 6. HTMX et Alpine.js via CDN

**Choix :** Chargement via `<script>` CDN dans `base.html`

**Raison :** Ces libs sont des fichiers JS uniques, legers. Pas de build step necessaire. En prod, on peut copier les fichiers en local dans `static/js/` si besoin.

### 7. PostgreSQL 16 en dev via Docker Compose

**Choix :** Service `db` PostgreSQL dans `docker-compose.yml`, Django se connecte via `DATABASE_URL`

**Raison :** Meme moteur en dev et en prod. Evite les surprises SQLite (pas de support JSON natif identique, pas de contraintes identiques).

## Risks / Trade-offs

- **[Risk] Tailwind CLI standalone pas dispo pour Windows ARM** → Mitigation : utiliser le CDN en fallback dev, ou installer via npm en dernier recours. Les VPS prod sont Linux x86.

- **[Risk] Modeles trop anticipes vs besoins reels** → Mitigation : on suit exactement le modele de donnees du PRD et de l'ARCHITECTURE.md, pas d'invention. Les champs sont documentes.

- **[Risk] django-allauth overhead pour 2-3 utilisateurs** → Mitigation : allauth gere bien le login basique. Si trop complexe, fallback vers `django.contrib.auth` natif avec vues custom. La configuration est minimale.

- **[Trade-off] Pas de fixtures metier dans cette change** → On pose les modeles mais pas de donnees. Les tests des changes suivantes devront creer leurs propres donnees. C'est voulu : chaque change est autonome.
