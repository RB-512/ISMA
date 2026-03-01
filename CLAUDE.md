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

<!-- rtk-instructions v2 -->
# RTK (Rust Token Killer) - Token-Optimized Commands

## Golden Rule

**Always prefix commands with `rtk`**. If RTK has a dedicated filter, it uses it. If not, it passes through unchanged. This means RTK is always safe to use.

**Important**: Even in command chains with `&&`, use `rtk`:
```bash
# ❌ Wrong
git add . && git commit -m "msg" && git push

# ✅ Correct
rtk git add . && rtk git commit -m "msg" && rtk git push
```

## RTK Commands by Workflow

### Build & Compile (80-90% savings)
```bash
rtk cargo build         # Cargo build output
rtk cargo check         # Cargo check output
rtk cargo clippy        # Clippy warnings grouped by file (80%)
rtk tsc                 # TypeScript errors grouped by file/code (83%)
rtk lint                # ESLint/Biome violations grouped (84%)
rtk prettier --check    # Files needing format only (70%)
rtk next build          # Next.js build with route metrics (87%)
```

### Test (90-99% savings)
```bash
rtk cargo test          # Cargo test failures only (90%)
rtk vitest run          # Vitest failures only (99.5%)
rtk playwright test     # Playwright failures only (94%)
rtk test <cmd>          # Generic test wrapper - failures only
```

### Git (59-80% savings)
```bash
rtk git status          # Compact status
rtk git log             # Compact log (works with all git flags)
rtk git diff            # Compact diff (80%)
rtk git show            # Compact show (80%)
rtk git add             # Ultra-compact confirmations (59%)
rtk git commit          # Ultra-compact confirmations (59%)
rtk git push            # Ultra-compact confirmations
rtk git pull            # Ultra-compact confirmations
rtk git branch          # Compact branch list
rtk git fetch           # Compact fetch
rtk git stash           # Compact stash
rtk git worktree        # Compact worktree
```

Note: Git passthrough works for ALL subcommands, even those not explicitly listed.

### GitHub (26-87% savings)
```bash
rtk gh pr view <num>    # Compact PR view (87%)
rtk gh pr checks        # Compact PR checks (79%)
rtk gh run list         # Compact workflow runs (82%)
rtk gh issue list       # Compact issue list (80%)
rtk gh api              # Compact API responses (26%)
```

### JavaScript/TypeScript Tooling (70-90% savings)
```bash
rtk pnpm list           # Compact dependency tree (70%)
rtk pnpm outdated       # Compact outdated packages (80%)
rtk pnpm install        # Compact install output (90%)
rtk npm run <script>    # Compact npm script output
rtk npx <cmd>           # Compact npx command output
rtk prisma              # Prisma without ASCII art (88%)
```

### Files & Search (60-75% savings)
```bash
rtk ls <path>           # Tree format, compact (65%)
rtk read <file>         # Code reading with filtering (60%)
rtk grep <pattern>      # Search grouped by file (75%)
rtk find <pattern>      # Find grouped by directory (70%)
```

### Analysis & Debug (70-90% savings)
```bash
rtk err <cmd>           # Filter errors only from any command
rtk log <file>          # Deduplicated logs with counts
rtk json <file>         # JSON structure without values
rtk deps                # Dependency overview
rtk env                 # Environment variables compact
rtk summary <cmd>       # Smart summary of command output
rtk diff                # Ultra-compact diffs
```

### Infrastructure (85% savings)
```bash
rtk docker ps           # Compact container list
rtk docker images       # Compact image list
rtk docker logs <c>     # Deduplicated logs
rtk kubectl get         # Compact resource list
rtk kubectl logs        # Deduplicated pod logs
```

### Network (65-70% savings)
```bash
rtk curl <url>          # Compact HTTP responses (70%)
rtk wget <url>          # Compact download output (65%)
```

### Meta Commands
```bash
rtk gain                # View token savings statistics
rtk gain --history      # View command history with savings
rtk discover            # Analyze Claude Code sessions for missed RTK usage
rtk proxy <cmd>         # Run command without filtering (for debugging)
rtk init                # Add RTK instructions to CLAUDE.md
rtk init --global       # Add RTK to ~/.claude/CLAUDE.md
```

## Token Savings Overview

| Category | Commands | Typical Savings |
|----------|----------|-----------------|
| Tests | vitest, playwright, cargo test | 90-99% |
| Build | next, tsc, lint, prettier | 70-87% |
| Git | status, log, diff, add, commit | 59-80% |
| GitHub | gh pr, gh run, gh issue | 26-87% |
| Package Managers | pnpm, npm, npx | 70-90% |
| Files | ls, read, grep, find | 60-75% |
| Infrastructure | docker, kubectl | 85% |
| Network | curl, wget | 65-70% |

Overall average: **60-90% token reduction** on common development operations.
<!-- /rtk-instructions -->