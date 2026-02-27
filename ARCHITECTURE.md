# Architecture technique — BDC Peinture MVP 1.0

**Date :** 27 février 2026
**Statut :** Validé
**Référence :** PRD.md, TECH_STACK_REPORT.md

---

## 1. Vue d'ensemble

```
┌─────────────────────────────────────────────────────────┐
│                      Navigateur                         │
│         (Secrétaire, CDT — 2 à 3 utilisateurs)         │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────┐
│                    Nginx (reverse proxy + SSL)           │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                 Gunicorn (WSGI)                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Django 5.x                                             │
│  ├── Templates + HTMX + Alpine.js + Tailwind CSS        │
│  ├── Django ORM                                         │
│  ├── pdfplumber (extraction PDF)                        │
│  └── Auth + Permissions (RBAC)                          │
│                                                         │
├─────────────┬───────────────────────┬───────────────────┤
│             │                       │                   │
│   PostgreSQL 16              Fichiers locaux      API externes
│   (données)                  /media/ (PDFs)       (SMS, Email)
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Choix d'architecture :** monolithe Django. Un seul projet, un seul langage (Python), un seul serveur. Justifié par le volume (2-3 utilisateurs, 150 BDC/mois) et la priorité à la simplicité de développement et de maintenance.

**Pas de tâches asynchrones en MVP.** L'envoi SMS, l'extraction PDF et toutes les opérations se font de manière synchrone dans la requête HTTP. Le volume est trop faible pour justifier Celery + Redis. Celery sera ajouté en V2 si le besoin se présente.

---

## 2. Stack technique

### 2.1 Backend

| Composant | Technologie | Version | Rôle |
|-----------|-------------|---------|------|
| Framework | **Django** | 5.x | Framework web principal |
| Serveur WSGI | **Gunicorn** | dernière | Serveur d'application Python |
| ORM | **Django ORM** | intégré | Accès base de données, migrations |
| Formulaires | **Django Forms** | intégré | Validation et rendu des formulaires |
| Filtres | **django-filter** | dernière | Filtrage du tableau de bord |
| Auth | **django-allauth** | dernière | Authentification (login, sessions) |
| Permissions | **Système de groupes Django** | intégré | RBAC via groupes (Secrétaire, CDT) |
| Extraction PDF | **pdfplumber** | dernière | Parser principal pour les tableaux PDF |
| Extraction PDF (fallback) | **PyMuPDF (fitz)** | dernière | Fallback si pdfplumber échoue |
| Génération PDF | **ReportLab** ou **WeasyPrint** | dernière | BDC terrain ERILIA (version sans prix) |

### 2.2 Frontend

| Composant | Technologie | Version | Rôle |
|-----------|-------------|---------|------|
| Templates | **Django Templates** | intégré | Rendu HTML côté serveur |
| Interactivité | **HTMX** | 2.x | Requêtes AJAX déclaratives, mises à jour partielles |
| JS léger | **Alpine.js** | 3.x | Interactions client (modales, dropdowns, toggles) |
| CSS | **Tailwind CSS** | 3.x | Framework utilitaire CSS |
| Icônes | **Heroicons** ou **Lucide** | dernière | Iconographie UI |
| PDF viewer | **Intégré navigateur** | — | `<iframe>` ou `<embed>` pour consultation du PDF original |

**Pas de build step JS.** HTMX, Alpine.js et Tailwind (via CDN ou CLI standalone) sont chargés directement. Pas de node_modules, pas de bundler, pas de webpack/vite.

> **Note Tailwind CSS :** utiliser le CLI standalone de Tailwind (`tailwindcss` binaire) pour générer le CSS en développement et en production, sans dépendance Node.js.

### 2.3 Base de données

| Composant | Technologie | Version |
|-----------|-------------|---------|
| SGBD | **PostgreSQL** | 16 |
| Driver Python | **psycopg** | 3.x (psycopg3) |

PostgreSQL est choisi pour sa robustesse, le support natif JSON (utile pour les données extraites du PDF), et le full-text search (recherche dans les BDC).

### 2.4 Infrastructure

| Composant | Technologie | Rôle |
|-----------|-------------|------|
| Serveur | **VPS OVH** ou **Scaleway** | Hébergement (France, RGPD) |
| Conteneurisation | **Docker + Docker Compose** | Déploiement reproductible |
| Reverse proxy | **Nginx** | HTTPS, fichiers statiques, proxy vers Gunicorn |
| SSL | **Let's Encrypt (Certbot)** | Certificat HTTPS gratuit |
| Stockage fichiers | **Local /media/** | PDFs uploadés sur le filesystem du VPS |
| Backups DB | **pg_dump** (cron quotidien) | Sauvegarde PostgreSQL |
| Backups fichiers | **rsync** ou **rclone** | Sauvegarde des PDFs vers stockage distant |

### 2.5 Outillage développement

| Outil | Rôle |
|-------|------|
| **uv** | Gestionnaire de dépendances et environnements Python |
| **Ruff** | Linter + formatter (remplace flake8, isort, black) |
| **pytest + pytest-django** | Tests unitaires et d'intégration |
| **Git + GitHub** | Gestion de code source |
| **GitHub Actions** | CI (tests, lint) |
| **Docker Compose** | Environnement de dev local (PostgreSQL) |

---

## 3. Modèle de données

### 3.1 Diagramme des entités

```
┌─────────────┐       ┌──────────────────────────────────────┐
│   User      │       │         BonDeCommande                │
│ (Django)    │       │                                      │
├─────────────┤       ├──────────────────────────────────────┤
│ username    │       │ id (PK, auto)                        │
│ email       │──────►│ cree_par (FK User)                   │
│ groups ─────┤       │                                      │
│  (Secrétaire│       │ # Identification                     │
│   ou CDT)   │       │ numero_bdc (unique)                  │
└─────────────┘       │ numero_marche                        │
                      │ bailleur (FK Bailleur)               │
                      │ date_emission                        │
┌─────────────┐       │                                      │
│  Bailleur   │       │ # Localisation                       │
├─────────────┤       │ programme_residence                  │
│ id (PK)     │◄──────│ adresse                              │
│ nom         │       │ code_postal                          │
│ code (GDH,  │       │ ville                                │
│  ERILIA)    │       │ logement_numero                      │
└─────────────┘       │ logement_type                        │
                      │ logement_etage                       │
                      │ logement_porte                       │
┌─────────────┐       │                                      │
│ SousTraitant│       │ # Travaux                            │
├─────────────┤       │ objet_travaux (text)                 │
│ id (PK)     │◄──────│ delai_execution (date)               │
│ nom         │       │                                      │
│ telephone   │       │ # Contacts                           │
│ email       │       │ occupant_nom                         │
│ actif (bool)│       │ occupant_telephone                   │
└─────────────┘       │ occupant_email                       │
      │               │ emetteur_nom                         │
      │               │ emetteur_telephone                   │
      │               │                                      │
      │               │ # Montants (confidentiels)           │
      │               │ montant_ht (Decimal)                 │
      │               │ montant_tva (Decimal)                │
      │               │ montant_ttc (Decimal)                │
      │               │                                      │
      │               │ # Infos manuelles                    │
      │               │ occupation (VACANT/OCCUPE)           │
      │               │ modalite_acces (text, nullable)      │
      │               │ rdv_pris (bool)                      │
      │               │ rdv_date (datetime, nullable)        │
      │               │ notes (text, nullable)               │
      │               │                                      │
      │               │ # Workflow                           │
      │               │ statut (choix: voir §3.2)            │
      └──────────────►│ sous_traitant (FK ST, nullable)      │
                      │ montant_st (Decimal, nullable)       │
                      │ pourcentage_st (Decimal, nullable)   │
                      │                                      │
                      │ # Fichiers                           │
                      │ pdf_original (FileField)             │
                      │                                      │
                      │ # Horodatage                         │
                      │ created_at (auto)                    │
                      │ updated_at (auto)                    │
                      └──────────┬───────────────────────────┘
                                 │
                                 │ 1:N
                    ┌────────────▼────────────┐
                    │   LignePrestation       │
                    ├─────────────────────────┤
                    │ id (PK)                 │
                    │ bdc (FK BonDeCommande)  │
                    │ designation (text)      │
                    │ quantite (Decimal)      │
                    │ unite (text)            │
                    │ prix_unitaire (Decimal) │
                    │ montant (Decimal)       │
                    │ ordre (int)             │
                    └─────────────────────────┘

                    ┌────────────────────────────────┐
                    │   HistoriqueAction              │
                    ├────────────────────────────────┤
                    │ id (PK)                        │
                    │ bdc (FK BonDeCommande)          │
                    │ utilisateur (FK User)           │
                    │ action (choix: voir §3.3)       │
                    │ details (JSONField, nullable)   │
                    │ created_at (auto)               │
                    └────────────────────────────────┘
```

### 3.2 Statuts du workflow

Les statuts suivent le cycle de vie du BDC et correspondent aux pochettes papier actuelles.

```
  ┌───────────┐     ┌──────────┐     ┌──────────┐     ┌────────────┐     ┌──────────┐
  │ A_TRAITER │────►│ A_FAIRE  │────►│ EN_COURS │────►│ A_FACTURER │────►│ FACTURE  │
  └───────────┘     └──────────┘     └──────────┘     └────────────┘     └──────────┘
       (1-2)            (2)            (3-6)               (7)
```

| Valeur DB | Label affiché | Pochette équivalente | Qui peut transitionner |
|-----------|---------------|---------------------|----------------------|
| `A_TRAITER` | A traiter | A traiter | Secrétaire (lors de la création) |
| `A_FAIRE` | A faire | A faire | Secrétaire (quand BDC complet) |
| `EN_COURS` | En cours | En cours | CDT (lors de l'attribution) |
| `A_FACTURER` | A facturer | A facturer | CDT (après validation réalisation) |
| `FACTURE` | Facturé | — | CDT (après rapprochement facturation) |

**Transitions autorisées :**

```python
TRANSITIONS = {
    "A_TRAITER":  ["A_FAIRE"],
    "A_FAIRE":    ["A_TRAITER", "EN_COURS"],    # retour possible si infos manquantes
    "EN_COURS":   ["A_FAIRE", "A_FACTURER"],     # retour si réattribution annule
    "A_FACTURER": ["EN_COURS", "FACTURE"],       # retour si erreur
    "FACTURE":    [],                              # état terminal
}
```

### 3.3 Types d'actions historisées

| Action | Description |
|--------|-------------|
| `CREATION` | BDC créé (upload PDF) |
| `MODIFICATION` | Champ(s) modifié(s) — détails en JSON |
| `STATUT_CHANGE` | Transition de statut — ancien et nouveau statut en JSON |
| `ATTRIBUTION` | Attribution à un ST — ST et montant en JSON |
| `REATTRIBUTION` | Changement de ST — ancien ST, nouveau ST en JSON |
| `NOTIFICATION_SMS` | SMS envoyé au ST — numéro et contenu en JSON |
| `VALIDATION` | CDT valide la réalisation |
| `FACTURATION` | Passage en facturé |

---

## 4. Extraction PDF

### 4.1 Stratégie

Un parser dédié par bailleur, car les formats PDF sont différents. Chaque parser hérite d'une classe de base commune.

```
pdf_extraction/
├── base.py             # Classe abstraite PDFParser
├── gdh_parser.py       # Parser GDH (Grand Delta Habitat)
├── erilia_parser.py    # Parser ERILIA
└── detector.py         # Détecte le type de PDF et route vers le bon parser
```

### 4.2 Bibliothèques

| Bibliothèque | Rôle | Justification |
|---------------|------|---------------|
| **pdfplumber** | Parser principal | Extraction de tableaux avec coordonnées de cellules. Peut identifier colonnes (désignation, qté, PU, montant) dans les lignes de prestation. |
| **PyMuPDF (fitz)** | Fallback | Extraction de texte brut avec blocs positionnés. Utilisé si pdfplumber échoue sur un format inattendu. |

### 4.3 Flux d'extraction

```
PDF uploadé
    │
    ▼
detector.py — Analyse la première page pour identifier le bailleur
    │
    ├── "Grand Delta Habitat" détecté ──► GDHParser
    │                                        │
    │                                        ├── Page 1 : extraction données complètes
    │                                        │   (numéro, adresse, prestations, montants...)
    │                                        │
    │                                        └── Page 2 : conservée telle quelle
    │                                            (= BDC terrain, déjà sans prix)
    │
    └── "ERILIA" détecté ──► ERILIAParser
                                │
                                ├── Extraction données complètes
                                │   (numéro, adresse, prestations, montants...)
                                │
                                └── Pas de page terrain
                                    (sera générée par l'app, voir §4.4)
    │
    ▼
Résultat : dict Python avec toutes les données structurées
    │
    ▼
Formulaire pré-rempli affiché à la secrétaire pour vérification
```

### 4.4 Génération du BDC terrain (sans prix)

| Bailleur | Stratégie |
|----------|-----------|
| **GDH** | Extraire la page 2 du PDF original avec PyMuPDF. C'est le bon d'intervention, déjà sans prix. |
| **ERILIA** | Générer un PDF à partir des données extraites, en omettant tous les champs de prix (PU, montants, totaux). Utiliser **WeasyPrint** (HTML → PDF) ou **ReportLab**. |

---

## 5. Authentification et rôles

### 5.1 Mécanisme

- **django-allauth** pour l'authentification (login email/mot de passe, gestion de session)
- **Groupes Django** pour les rôles : chaque utilisateur appartient à un groupe qui détermine ses permissions
- Les comptes sont créés par un administrateur (pas d'inscription publique)

### 5.2 Groupes et permissions

| Groupe | Permissions |
|--------|------------|
| **Secrétaire** | Créer un BDC, modifier un BDC, voir le tableau de bord, voir les prix, transition A_TRAITER ↔ A_FAIRE |
| **CDT** | Toutes les permissions Secrétaire + attribuer, réattribuer, valider, facturer, toutes les transitions de statut |

> **Direction (V2)** : groupe en lecture seule sur le tableau de bord et les prix. Hors périmètre MVP.

### 5.3 Contrôle d'accès

Le contrôle se fait via des **décorateurs** et des **mixins** Django sur les vues :

```python
# Exemple : seul le CDT peut attribuer
@group_required("CDT")
def attribuer_bdc(request, bdc_id):
    ...
```

Un mixin `GroupRequiredMixin` sera implémenté pour les vues basées sur des classes.

---

## 6. Notifications externes

### 6.1 SMS

| Aspect | Choix |
|--------|-------|
| Fournisseur | **A définir** — OVH SMS (~0.05€/SMS, hébergement FR) ou Twilio (plus de documentation, ~0.07€/SMS) |
| Déclenchement | Synchrone, au moment de l'attribution du BDC |
| Contenu | Adresse, type de logement, vacant/occupé, modalité d'accès, RDV, objet des travaux. **Jamais de prix.** |

### 6.2 Email

| Aspect | Choix |
|--------|-------|
| Fournisseur | **Django `send_mail`** via SMTP (serveur mail existant ou SendGrid/Mailgun) |
| Usage MVP | Envoi du BDC terrain en PDF en pièce jointe (complément du SMS) |

### 6.3 Abstraction

Un module `notifications/` encapsule l'envoi :

```python
# notifications/sms.py
def envoyer_sms_attribution(bdc: BonDeCommande) -> bool:
    """Envoie le SMS d'attribution au ST. Retourne True si succès."""
    ...

# notifications/email.py
def envoyer_email_bdc_terrain(bdc: BonDeCommande) -> bool:
    """Envoie le BDC terrain PDF par email au ST."""
    ...
```

Si le SMS échoue, l'erreur est loguée et l'utilisateur est notifié dans l'interface (pas de retry automatique en MVP).

---

## 7. Stockage fichiers

### 7.1 Stratégie

Stockage local sur le filesystem du VPS dans le répertoire `MEDIA_ROOT` de Django.

```
/media/
└── bdc/
    └── <annee>/
        └── <mois>/
            ├── 450056_original.pdf        # PDF original uploadé
            └── 450056_terrain.pdf          # BDC terrain généré (ERILIA)
```

### 7.2 Configuration Django

```python
MEDIA_ROOT = "/data/media/"       # Volume Docker persistant
MEDIA_URL = "/media/"
```

### 7.3 Sécurité

Les fichiers PDF ne sont **pas** servis directement par Nginx. Django vérifie les permissions de l'utilisateur avant de servir le fichier (via une vue protégée). Cela empêche l'accès non authentifié aux PDFs.

### 7.4 Sauvegarde

- Backup quotidien du dossier `/data/media/` via **rsync** ou **rclone** vers un stockage distant
- Le volume est faible : ~150 PDFs/mois × ~200 Ko ≈ 30 Mo/mois

---

## 8. Structure du projet

```
bdc-peinture/
├── pyproject.toml                 # Dépendances (uv)
├── uv.lock                        # Lock file
├── Dockerfile
├── docker-compose.yml             # PostgreSQL + app
├── .env.example
├── manage.py
│
├── config/                        # Configuration Django
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py                # Settings communs
│   │   ├── dev.py                 # Développement (DEBUG=True)
│   │   └── prod.py                # Production (sécurité, HTTPS)
│   ├── urls.py                    # Routes principales
│   └── wsgi.py
│
├── apps/
│   ├── accounts/                  # Utilisateurs et rôles
│   │   ├── models.py              # Profil utilisateur si nécessaire
│   │   ├── views.py               # Login, logout
│   │   ├── forms.py
│   │   ├── urls.py
│   │   └── decorators.py          # @group_required
│   │
│   ├── bdc/                       # Coeur métier
│   │   ├── models.py              # BonDeCommande, LignePrestation, HistoriqueAction
│   │   ├── views.py               # CRUD, dashboard, transitions de statut
│   │   ├── forms.py               # Formulaire BDC (création, édition)
│   │   ├── filters.py             # Filtres tableau de bord (django-filter)
│   │   ├── services.py            # Logique métier (workflow, attribution, validation)
│   │   ├── urls.py
│   │   └── admin.py               # Admin Django (debug, gestion ponctuelle)
│   │
│   ├── pdf_extraction/            # Extraction de données PDF
│   │   ├── base.py                # Classe abstraite PDFParser
│   │   ├── gdh_parser.py
│   │   ├── erilia_parser.py
│   │   └── detector.py            # Auto-détection du type de PDF
│   │
│   ├── sous_traitants/            # Gestion des sous-traitants
│   │   ├── models.py              # SousTraitant
│   │   ├── views.py               # Liste, CRUD
│   │   ├── urls.py
│   │   └── admin.py
│   │
│   └── notifications/             # SMS et email
│       ├── sms.py
│       └── email.py
│
├── templates/
│   ├── base.html                  # Layout principal (nav, sidebar, Tailwind)
│   ├── accounts/
│   │   └── login.html
│   ├── bdc/
│   │   ├── dashboard.html         # Tableau de bord principal
│   │   ├── detail.html            # Fiche BDC complète
│   │   ├── form_create.html       # Création (upload + formulaire)
│   │   ├── form_edit.html         # Edition
│   │   ├── attribution.html       # Formulaire d'attribution
│   │   └── partials/              # Fragments HTMX
│   │       ├── bdc_table.html     # Tableau filtrable (rechargé par HTMX)
│   │       ├── bdc_row.html       # Ligne individuelle
│   │       └── status_badge.html  # Badge de statut coloré
│   └── sous_traitants/
│       └── list.html
│
├── static/
│   ├── css/
│   │   └── output.css             # CSS généré par Tailwind CLI
│   ├── js/                        # Scripts custom si nécessaire
│   └── img/
│
└── tests/
    ├── conftest.py                # Fixtures pytest
    ├── test_pdf_extraction/
    │   ├── test_gdh_parser.py
    │   ├── test_erilia_parser.py
    │   └── fixtures/              # PDFs de test (vrais exemples anonymisés)
    ├── test_bdc/
    │   ├── test_models.py
    │   ├── test_views.py
    │   ├── test_workflow.py       # Tests des transitions de statut
    │   └── test_forms.py
    └── test_notifications/
        └── test_sms.py
```

---

## 9. Déploiement

### 9.1 Docker Compose (production)

```yaml
# Aperçu de la configuration
services:
  web:           # Django + Gunicorn
  nginx:         # Reverse proxy + SSL + statiques
  db:            # PostgreSQL 16
```

Trois conteneurs, un seul `docker-compose.yml`. Démarrage avec `docker compose up -d`.

### 9.2 Environnement de développement

```bash
# Setup initial
uv sync                            # Installe les dépendances
docker compose up db -d             # Lance PostgreSQL seul
uv run manage.py migrate            # Applique les migrations
uv run manage.py createsuperuser    # Crée le premier utilisateur
uv run manage.py runserver          # Lance le serveur de dev
```

### 9.3 CI/CD (GitHub Actions)

| Étape | Contenu |
|-------|---------|
| **Lint** | `ruff check .` + `ruff format --check .` |
| **Tests** | `pytest` avec PostgreSQL en service |
| **Déploiement** | SSH vers le VPS, `git pull`, `docker compose up -d --build` |

---

## 10. Conventions de développement

### 10.1 Python / Django

- **Python 3.12+**
- **Ruff** pour le linting et le formatage (configuration dans `pyproject.toml`)
- **pytest** pour tous les tests (pas `unittest`)
- Logique métier dans `services.py`, pas dans les vues ni les modèles
- Nommage des modèles en français (les termes métier sont en français dans le PRD)
- Nommage des variables et fonctions en snake_case, en français pour le domaine métier, en anglais pour le technique

### 10.2 Templates / Frontend

- Un template `base.html` avec blocs `{% block content %}`, `{% block title %}`
- Fragments HTMX dans `templates/<app>/partials/`
- Attributs HTMX directement dans le HTML (`hx-get`, `hx-target`, `hx-swap`)
- Alpine.js pour les interactions purement client (toggle, modales, dropdowns)
- Classes Tailwind directement dans les templates (pas de CSS custom sauf cas exceptionnel)

### 10.3 Git

- Branche `main` = production
- Branches de feature : `feature/<nom>`
- Commits en français, format : `<type>: <description>` (ex: `feat: ajout extraction PDF GDH`)

---

## 11. Sécurité

| Mesure | Implémentation |
|--------|----------------|
| CSRF | Middleware Django (activé par défaut) |
| XSS | Auto-escaping Django Templates (activé par défaut) |
| SQL injection | Django ORM (requêtes paramétrées) |
| HTTPS | Let's Encrypt via Nginx |
| Auth | Sessions Django (cookie httponly, secure) |
| Upload fichiers | Validation type MIME (PDF uniquement), limite de taille |
| Accès fichiers | PDFs servis via vue Django protégée, pas en accès direct Nginx |
| Mots de passe | Hashage bcrypt via Django, validation de complexité |
| Prix confidentiels | Jamais inclus dans les templates BDC terrain, vérification côté serveur |

---

## 12. Décisions reportées à V2+

Ces points sont identifiés mais explicitement hors périmètre MVP. L'architecture est conçue pour les accueillir sans refonte.

| Point | Phase | Impact architecture |
|-------|-------|-------------------|
| Espace sous-traitant (accès web restreint) | V2 | Ajout d'un groupe "ST" + vues dédiées. Modèle de données déjà prêt. |
| Tâches asynchrones (Celery + Redis) | V2 | Ajout de 2 services dans Docker Compose. Les fonctions `envoyer_sms_*` deviennent des tasks Celery. |
| Import automatique IKOS | V2 | Nouveau module `apps/import_ikos/` avec scraping ou API. |
| Import email ERILIA | V2 | Nouveau module `apps/import_email/` avec IMAP. |
| Stockage objet S3 | V2 | Changer `DEFAULT_FILE_STORAGE` dans settings. Transparent pour le code. |
| Application mobile / PWA | V3 | Ajouter Django Ninja (API JSON) en parallèle des vues HTML. Le frontend mobile consomme l'API. |
| Statistiques avancées | V3 | Vues dashboard supplémentaires + Chart.js. |
