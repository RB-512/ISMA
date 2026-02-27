# Rapport Tech Stack — BDC Peinture MVP 1.0

**Date :** 27 février 2026
**Contexte :** Choix du stack technique pour l'application BDC Peinture
**Basé sur :** PRD.md — MVP 1.0

---

## 1. Exigences techniques clés (issues du PRD)

Avant de comparer les options, identifions les contraintes techniques déterminantes :

| Exigence | Criticité | Impact sur le choix |
|----------|-----------|---------------------|
| **Extraction de données PDF** (tables, montants, adresses) | **CRITIQUE** | Le coeur technique du MVP. Deux formats PDF différents (GDH, ERILIA) avec des structures distinctes. |
| Application web navigateur | Haute | Tout framework web convient |
| Gestion de workflow (7 étapes, transitions, règles métier) | Haute | Nécessite une modélisation propre des états |
| Rôles et permissions (Secrétaire, CDT, Direction) | Haute | Auth + RBAC nécessaires |
| Stockage fichiers PDF | Moyenne | Upload + stockage + consultation |
| Tableau de bord avec filtres (statut, bailleur, ST) | Haute | UI interactive requise |
| Historique / audit log | Moyenne | Traçabilité de chaque action |
| Notifications SMS/email aux ST | Moyenne | API externe (Twilio, etc.) |
| Interface 100% français | Basse | i18n non nécessaire, juste du contenu FR |
| Volume : 50-150 BDC/mois, 2-3 utilisateurs | Info | La performance n'est PAS un enjeu |

**Conclusion clé : l'extraction PDF est LE différenciateur technique.**
Les PDF sont numériques (pas des scans), ce qui simplifie l'extraction, mais il faut parser des tableaux de prestations avec lignes, quantités, prix unitaires et montants — c'est non-trivial.

---

## 2. Les 5 options comparées

### Option A — Next.js Full-Stack (TypeScript pur)

```
┌─────────────────────────────────────────┐
│           Next.js 14+ (App Router)      │
│  ┌──────────┐  ┌──────────────────────┐ │
│  │  React    │  │  API Routes / Server │ │
│  │  (UI)     │  │  Actions (Backend)   │ │
│  └──────────┘  └──────────────────────┘ │
│         │               │               │
│         └───────┬───────┘               │
│                 ▼                        │
│          PostgreSQL + Prisma ORM        │
│          NextAuth.js (Auth)             │
│          pdf-parse / pdf.js (PDF)       │
└─────────────────────────────────────────┘
Déploiement : Vercel ou VPS + Docker
```

**Stack :** Next.js 14+ (App Router) · React · Tailwind CSS · PostgreSQL · Prisma ORM · NextAuth.js · pdf-parse

| Avantage | Inconvénient |
|----------|-------------|
| Un seul langage (TypeScript) partout | **Extraction PDF médiocre en JS** — `pdf-parse` extrait du texte brut, très mauvais pour les tableaux |
| Écosystème React gigantesque | Pas d'admin panel intégré |
| Server Components pour le rendu | Gestion de fichiers plus complexe qu'en Python |
| Prisma simplifie la DB | Auth + rôles à construire manuellement |
| Déploiement Vercel très simple | Server Actions encore jeunes pour du CRUD complexe |

**Verdict PDF :** `pdf-parse` retourne du texte linéaire sans notion de position, colonnes ou tableaux. Pour parser les lignes de prestation (désignation + quantité + PU + montant), il faudrait du regex fragile ou un appel à un service externe (API OCR/LLM). **C'est le point faible majeur.**

---

### Option B — Django Monolithe + HTMX (Python pur)

```
┌─────────────────────────────────────────┐
│              Django 5.x                 │
│  ┌──────────────────────────────────┐   │
│  │  Django Templates + HTMX        │   │
│  │  + Alpine.js + Tailwind CSS     │   │
│  │  (UI dynamique côté serveur)    │   │
│  └──────────────────────────────────┘   │
│                 │                        │
│  ┌──────────────────────────────────┐   │
│  │  Django ORM + Auth + Admin      │   │
│  │  pdfplumber / tabula-py (PDF)   │   │
│  └──────────────────────────────────┘   │
│                 │                        │
│          PostgreSQL                     │
└─────────────────────────────────────────┘
Déploiement : VPS (OVH/Scaleway) + Docker
```

**Stack :** Django 5.x · HTMX · Alpine.js · Tailwind CSS · PostgreSQL · pdfplumber · tabula-py

| Avantage | Inconvénient |
|----------|-------------|
| **Extraction PDF excellente** — pdfplumber parse les tableaux nativement | UI moins riche qu'un SPA React |
| Un seul projet, un seul langage (Python) | HTMX = paradigme différent (courbe d'apprentissage) |
| Django Admin intégré (debug, gestion données) | Interactions complexes (drag & drop, filtres dynamiques) plus limitées |
| Auth + permissions + RBAC intégrés | Moins de composants UI prêts à l'emploi |
| ORM puissant + migrations automatiques | Rechargement de page partiel (pas un vrai SPA) |
| Architecture la plus simple à maintenir | |
| Développement le plus rapide | |

**Verdict PDF :** `pdfplumber` peut extraire les tableaux avec position exacte de chaque cellule. On peut parser les lignes de prestation, identifier les colonnes (désignation, qté, PU, montant), et structurer les données proprement. **C'est la meilleure option pour l'extraction PDF.**

---

### Option C — Django API + Next.js Frontend (Python + TypeScript)

```
┌─────────────────────┐     ┌─────────────────────┐
│   Next.js Frontend  │     │   Django Backend     │
│                     │     │                      │
│  React + Tailwind   │◄───►│  Django REST         │
│  shadcn/ui          │ API │  Framework           │
│  (SPA riche)        │JSON │  pdfplumber (PDF)    │
│                     │     │  Auth + Permissions   │
└─────────────────────┘     └──────────┬───────────┘
  Vercel / VPS                         │
                                 PostgreSQL
                                   VPS + Docker
```

**Stack :** Django REST Framework · Next.js 14+ · React · Tailwind CSS · shadcn/ui · PostgreSQL · pdfplumber · JWT (SimpleJWT)

| Avantage | Inconvénient |
|----------|-------------|
| **Extraction PDF excellente** (Python) | Deux projets séparés à maintenir |
| **UI riche** (React + shadcn/ui) | Deux langages (Python + TypeScript) |
| API réutilisable (future app mobile V3) | Déploiement plus complexe (2 apps) |
| Meilleur des deux mondes | Sérialisation API = overhead de code |
| Dashboard interactif et fluide | Auth JWT entre les deux = plus de config |
| Composants UI modernes prêts à l'emploi | Temps de développement plus long |

**Verdict PDF :** Même qualité que l'option B (Python côté serveur). L'extraction est gérée par le backend Django.

---

### Option D — Laravel + Vue.js / Inertia.js (PHP)

```
┌─────────────────────────────────────────┐
│           Laravel 11 + Inertia.js       │
│  ┌──────────┐  ┌──────────────────────┐ │
│  │  Vue 3   │  │  Laravel Backend     │ │
│  │  (UI)    │◄─│  Eloquent ORM        │ │
│  │ Tailwind │  │  Auth Breeze/Jetstr. │ │
│  └──────────┘  └──────────────────────┘ │
│         │               │               │
│         └───────┬───────┘               │
│                 ▼                        │
│          MySQL / PostgreSQL             │
│          Smalot/PdfParser (PDF)         │
└─────────────────────────────────────────┘
Déploiement : Hébergement PHP mutualisé ou VPS
```

**Stack :** Laravel 11 · Inertia.js · Vue 3 · Tailwind CSS · MySQL/PostgreSQL · Smalot/PdfParser

| Avantage | Inconvénient |
|----------|-------------|
| Laravel très productif (Eloquent, Artisan, Queues) | **Extraction PDF faible en PHP** |
| Inertia.js fusionne serveur + client élégamment | Smalot/PdfParser limité pour les tableaux |
| Vue.js approchable et réactif | Écosystème PDF nettement inférieur à Python |
| Auth Breeze/Jetstream clé en main | PHP moins populaire pour les nouveaux projets |
| Hébergement PHP très abordable | Moins de momentum que l'écosystème JS/Python |
| Laravel Notifications (SMS, email) intégré | |

**Verdict PDF :** `Smalot/PdfParser` extrait du texte mais sans parsing de tableaux fiable. Il faudrait des workarounds significatifs ou un appel à un service Python externe — ce qui annule l'intérêt d'un stack PHP pur.

---

### Option E — Supabase + Next.js (BaaS)

```
┌─────────────────────┐     ┌─────────────────────┐
│   Next.js Frontend  │     │   Supabase (BaaS)   │
│                     │     │                      │
│  React + Tailwind   │◄───►│  PostgreSQL (géré)   │
│  shadcn/ui          │     │  Auth (intégré)      │
│                     │     │  Storage (fichiers)  │
│                     │     │  Edge Functions      │
└─────────────────────┘     │  Row Level Security  │
  Vercel                    └──────────────────────┘
```

**Stack :** Supabase · Next.js 14+ · React · Tailwind CSS · PostgreSQL (Supabase) · Edge Functions

| Avantage | Inconvénient |
|----------|-------------|
| Setup initial le plus rapide | **Extraction PDF quasi-impossible** en Edge Functions |
| Auth + stockage + DB out-of-the-box | Vendor lock-in (dépendance Supabase) |
| Row Level Security pour les rôles | Logique métier complexe difficile en Edge Functions |
| Realtime intégré | Coût mensuel qui grandit |
| Pas d'infrastructure à gérer | Requêtes complexes limitées par le client Supabase |
| | Workflow à 7 étapes = logique serveur lourde, mal adaptée au BaaS |

**Verdict PDF :** Les Edge Functions (Deno) n'ont pas de bibliothèque PDF sérieuse. Il faudrait un microservice Python séparé juste pour l'extraction, ce qui complexifie énormément l'architecture. **Éliminatoire.**

---

## 3. Comparaison détaillée

### 3.1 Grille de notation

Chaque critère est noté de 1 à 5 (5 = meilleur) et pondéré selon son importance pour le projet BDC Peinture.

| Critère | Poids | A (Next.js) | B (Django+HTMX) | C (Django+Next) | D (Laravel+Vue) | E (Supabase) |
|---------|-------|:-----------:|:----------------:|:----------------:|:----------------:|:------------:|
| **Extraction PDF** | **×5** | 1 | **5** | **5** | 2 | 1 |
| **Rapidité dev MVP** | **×4** | 3 | **5** | 3 | 4 | 4 |
| **Qualité UI/UX** | **×3** | **5** | 3 | **5** | 4 | **5** |
| **Simplicité architecture** | **×3** | 4 | **5** | 2 | 3 | 3 |
| **Auth & rôles** | **×2** | 3 | **5** | 4 | **5** | 4 |
| **Maintenabilité** | **×3** | 4 | **5** | 3 | 4 | 3 |
| **Déploiement** | **×2** | **5** | 4 | 3 | 4 | **5** |
| **Coût hébergement** | **×1** | 3 | **5** | 3 | **5** | 2 |
| **Évolutivité (V2-V4)** | **×2** | 4 | 3 | **5** | 4 | 3 |

### 3.2 Scores pondérés

| Option | Score brut | Score pondéré /125 | % |
|--------|-----------|-------------------|---|
| **A — Next.js Full-Stack** | 32 | 76 | 61% |
| **B — Django + HTMX** | **45** | **113** | **90%** |
| **C — Django API + Next.js** | 35 | 93 | 74% |
| **D — Laravel + Vue.js** | 35 | 88 | 70% |
| **E — Supabase + Next.js** | 30 | 75 | 60% |

### 3.3 Analyse par critère

#### Extraction PDF (poids ×5 — le plus important)

C'est le critère décisif. Voici un test concret : extraire une ligne de prestation comme :

```
M-P préparation et mise en peinture    15,00 m²    11,19 €    167,85 €
```

| Outil | Langage | Résultat |
|-------|---------|----------|
| **pdfplumber** | Python | Extraction par tableau avec coordonnées. Chaque cellule est identifiée. **Fiable.** |
| **tabula-py** | Python | Spécialisé tables PDF. Retourne un DataFrame pandas. **Excellent.** |
| **PyMuPDF (fitz)** | Python | Extraction texte avec blocs positionnés. Bon fallback. |
| pdf-parse | JavaScript | Texte brut linéaire. Les colonnes sont mélangées. **Inutilisable pour les tableaux.** |
| Smalot/PdfParser | PHP | Texte basique. Pas de notion de tableau. **Insuffisant.** |

**Python est 10× supérieur** pour cette tâche. C'est un fait technique, pas une préférence.

#### Rapidité de développement MVP (poids ×4)

Pour un MVP avec 2-3 utilisateurs et 50-150 enregistrements/mois :

- **Django (B)** : Admin intégré + ORM + Auth + Migrations + Forms = le plus rapide pour du CRUD/workflow
- **Laravel (D)** : Très proche de Django en productivité, Artisan + Eloquent sont excellents
- **Supabase (E)** : Setup immédiat, mais la logique workflow complexe ralentit ensuite
- **Next.js (A/C)** : Plus de plomberie à écrire (auth, permissions, formulaires)

#### Qualité UI/UX (poids ×3)

- **React (A, C, E)** : UI la plus riche, composants shadcn/ui, animations fluides
- **Vue + Inertia (D)** : Très bon, expérience SPA avec données serveur
- **HTMX (B)** : Fonctionnel mais moins fluide. Pour un dashboard avec filtres multiples et vue tableau, c'est suffisant mais pas aussi élégant qu'un SPA

---

## 4. Recommandation

### Choix recommandé : Option B — Django + HTMX + Tailwind CSS

```
┌──────────────────────────────────────────────────────────┐
│                    STACK RECOMMANDÉ                       │
│                                                          │
│   Django 5.x + HTMX + Alpine.js + Tailwind CSS          │
│   PostgreSQL + pdfplumber + Twilio (SMS)                 │
│                                                          │
│   Déploiement : VPS OVH/Scaleway + Docker + Nginx       │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│   Frontend        │  Backend          │  Infra           │
│   ─────────       │  ─────────        │  ─────────       │
│   Django Templates│  Django 5.x       │  PostgreSQL 16   │
│   HTMX 2.x       │  Django ORM       │  Docker + Nginx  │
│   Alpine.js 3.x  │  pdfplumber       │  VPS (OVH)       │
│   Tailwind CSS 3  │  django-allauth   │  Let's Encrypt   │
│   Chart.js        │  django-filter    │  Backups auto    │
│                   │  Twilio SDK       │                  │
│                   │  Celery (async)   │                  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Pourquoi cette option ?

**1. L'extraction PDF est le coeur technique du MVP.**
Chaque BDC passe par l'extraction. Si elle échoue, l'app entière perd son intérêt. Python est le seul écosystème avec des bibliothèques fiables pour parser des tableaux PDF. Avec `pdfplumber`, on peut :
- Identifier les zones du PDF (en-tête, tableau, totaux)
- Extraire chaque cellule d'un tableau avec ses coordonnées
- Gérer les deux formats différents (GDH et ERILIA) avec des parsers spécifiques

**2. Django est le framework le plus productif pour ce type d'app.**
BDC Peinture est une application CRUD avec workflow, rôles et formulaires — exactement ce pour quoi Django a été conçu. Voici ce qu'on obtient gratuitement :
- Admin panel (gestion données, debug, opérations ponctuelles)
- Système d'auth complet (login, sessions, permissions)
- ORM avec migrations automatiques
- Formulaires avec validation
- Middleware CSRF, XSS, SQL injection (sécurité intégrée)

**3. HTMX suffit largement pour les besoins UI.**
L'app a 2-3 utilisateurs, des tableaux filtrables et des formulaires. On n'a pas besoin d'un SPA React. HTMX permet :
- Filtrage dynamique du tableau de bord sans rechargement
- Soumission de formulaires en AJAX
- Mise à jour partielle de la page (statut d'un BDC, attribution)
- Le tout sans build step, sans node_modules, sans bundle

**4. Architecture la plus simple = la plus maintenable.**
Un seul projet, un seul langage, un seul serveur. Pas de synchronisation API frontend/backend, pas de gestion de tokens JWT, pas de deux déploiements à coordonner.

**5. Coût minimal.**
Un VPS OVH à ~5-10€/mois suffit largement pour 2-3 utilisateurs et 150 enregistrements/mois. Pas de services managés coûteux.

### Quand choisir l'Option C (Django + Next.js) à la place ?

Si les exigences UI évoluent fortement (V2-V3) vers :
- Un espace sous-traitant très interactif
- Des visualisations de données complexes
- Une PWA/application mobile
- Des interactions temps réel poussées

Dans ce cas, le frontend Next.js se justifie. Mais **pour le MVP**, c'est de la sur-ingénierie.

---

## 5. Stack détaillé recommandé

### 5.1 Backend

| Composant | Choix | Justification |
|-----------|-------|---------------|
| Framework | **Django 5.x** | Batteries included pour CRUD/workflow |
| ORM | **Django ORM** | Intégré, migrations auto, requêtes complexes |
| Auth | **django-allauth** | Login, sessions, extensible pour V2 |
| Permissions | **django-guardian** ou custom | Permission par objet si nécessaire |
| API (optionnel) | **Django Ninja** | Plus léger que DRF, si besoin d'endpoints JSON |
| Tâches async | **Celery + Redis** | Envoi SMS/email en arrière-plan |
| Filtres | **django-filter** | Filtrage tableau de bord |

### 5.2 Extraction PDF

| Composant | Choix | Justification |
|-----------|-------|---------------|
| Parser principal | **pdfplumber** | Extraction tableaux avec coordonnées |
| Parser fallback | **PyMuPDF (fitz)** | Extraction texte brut si pdfplumber échoue |
| Stratégie | **Un parser par bailleur** | Classe GDHParser + ERILIAParser, chacune connaissant la structure du PDF |

### 5.3 Frontend

| Composant | Choix | Justification |
|-----------|-------|---------------|
| Templates | **Django Templates** | Intégré, pas de build step |
| Interactivité | **HTMX 2.x** | Requêtes AJAX déclaratives, partials |
| JS léger | **Alpine.js 3.x** | Composants interactifs (modales, dropdowns, toggle) |
| CSS | **Tailwind CSS 3** | Utilitaire, rapide à styler |
| Tableaux | **Simple Datatables** ou custom HTMX | Tri, recherche, pagination |
| Graphiques | **Chart.js** | Dashboard stats (optionnel V1) |
| PDF viewer | **PDF.js (embed)** | Consultation du PDF original dans l'app |

### 5.4 Infrastructure

| Composant | Choix | Justification |
|-----------|-------|---------------|
| Base de données | **PostgreSQL 16** | Robuste, JSON natif, full-text search |
| Serveur | **VPS OVH / Scaleway** | Hébergement FR, RGPD, ~5-10€/mois |
| Conteneurisation | **Docker + Docker Compose** | Déploiement reproductible |
| Serveur web | **Nginx + Gunicorn** | Standard Django en production |
| SSL | **Let's Encrypt (Certbot)** | HTTPS gratuit |
| Fichiers | **Stockage local** ou **S3 (Scaleway Object Storage)** | PDFs uploadés |
| SMS | **Twilio** ou **OVH SMS** | API SMS pour notifications ST |
| Email | **SendGrid** ou **OVH Email** | Notifications email |

### 5.5 Développement

| Outil | Choix |
|-------|-------|
| Gestion de code | Git + GitHub |
| Environnement | Python 3.12+ · venv ou Poetry |
| Linter | Ruff (remplace flake8 + isort + black) |
| Tests | pytest + pytest-django |
| CI/CD | GitHub Actions (tests + déploiement) |

---

## 6. Estimation de la structure du projet

```
bdc-peinture/
├── manage.py
├── pyproject.toml
├── docker-compose.yml
├── Dockerfile
├── .env.example
│
├── config/                    # Configuration Django
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── urls.py
│   └── wsgi.py
│
├── apps/
│   ├── accounts/              # Auth, utilisateurs, rôles
│   │   ├── models.py
│   │   ├── views.py
│   │   └── ...
│   │
│   ├── bdc/                   # Coeur métier : BDC + workflow
│   │   ├── models.py          # BonDeCommande, LignePrestation, HistoriqueAction
│   │   ├── views.py           # CRUD, dashboard, transitions
│   │   ├── forms.py           # Formulaires BDC
│   │   ├── filters.py         # Filtres tableau de bord
│   │   ├── services.py        # Logique métier (workflow, attribution)
│   │   └── ...
│   │
│   ├── pdf_extraction/        # Extraction PDF
│   │   ├── base.py            # Classe abstraite BaseParser
│   │   ├── gdh_parser.py      # Parser spécifique GDH
│   │   ├── erilia_parser.py   # Parser spécifique ERILIA
│   │   └── ...
│   │
│   ├── sous_traitants/        # Gestion des ST
│   │   ├── models.py
│   │   └── ...
│   │
│   └── notifications/         # SMS + Email
│       ├── sms.py
│       ├── email.py
│       └── ...
│
├── templates/                 # Templates Django + HTMX
│   ├── base.html
│   ├── bdc/
│   │   ├── dashboard.html
│   │   ├── detail.html
│   │   ├── form.html
│   │   └── partials/          # Fragments HTMX
│   │       ├── bdc_table.html
│   │       ├── bdc_row.html
│   │       └── status_badge.html
│   └── ...
│
├── static/
│   ├── css/
│   ├── js/
│   └── ...
│
└── tests/
    ├── test_pdf_extraction/
    ├── test_bdc/
    └── ...
```

---

## 7. Risques et mitigations

| Risque | Probabilité | Mitigation |
|--------|------------|------------|
| Extraction PDF échoue sur certains formats | Moyenne | Deux parsers (pdfplumber + PyMuPDF fallback). Tests unitaires sur vrais PDFs GDH/ERILIA. Mode édition manuelle toujours disponible. |
| HTMX trop limité pour le dashboard | Basse | Alpine.js compense pour les interactions JS. Migration vers un frontend React possible sans toucher au backend (ajouter Django Ninja API). |
| Envoi SMS coûteux ou échoue | Basse | OVH SMS (~0.05€/SMS) comme alternative low-cost à Twilio. Fallback email. |
| Un seul développeur, maintenabilité | Moyenne | Django + conventions strictes + tests = code maintenable. Claude Code assiste efficacement sur Django/Python. |

---

## 8. Synthèse

```
                    Extraction     Rapidité      UI/UX      Simplicité
                       PDF          MVP
                        │            │             │             │
   A (Next.js)     ░░░░░░░░░░  ███████░░░  █████████░  ████████░░
   B (Django+HTMX) ██████████  ██████████  ██████░░░░  ██████████  ◄── RECOMMANDÉ
   C (Django+Next) ██████████  ██████░░░░  █████████░  ████░░░░░░
   D (Laravel+Vue) ███░░░░░░░  ████████░░  ████████░░  ██████░░░░
   E (Supabase)    ░░░░░░░░░░  ████████░░  █████████░  ██████░░░░
```

**Le choix est clair : Django + HTMX + Tailwind CSS + PostgreSQL + pdfplumber.**

C'est le stack qui offre le meilleur ratio entre la qualité d'extraction PDF (critique), la vitesse de développement du MVP, et la simplicité de maintenance pour une application métier de cette taille.
