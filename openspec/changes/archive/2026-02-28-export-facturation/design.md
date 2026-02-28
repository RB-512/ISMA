## Context

Le workflow BDC est complet de la réception à la facturation. Le CDT peut valider les réalisations et passer les BDC en facturation via l'écran de recoupement. Cependant, il n'existe aucun moyen d'extraire les données de facturation pour les transmettre à la comptabilité. Le CDT doit actuellement recopier manuellement les informations.

## Goals / Non-Goals

**Goals:**
- Permettre au CDT d'exporter un fichier Excel (.xlsx) des BDC à facturer / facturés
- Offrir des filtres par période, sous-traitant et statut
- Intégrer les liens d'export dans les écrans existants (recoupement, dashboard)

**Non-Goals:**
- Module de facturation complet (V3 selon PRD)
- Génération de factures PDF
- Export CSV (Excel couvre le besoin, CSV pourra être ajouté plus tard)
- Intégration avec un logiciel de comptabilité externe

## Decisions

### D1 — Format Excel via openpyxl
L'export se fait en `.xlsx` via la bibliothèque `openpyxl` (pure Python, pas de dépendance système). Alternative considérée : CSV — rejeté car le CDT travaille dans Excel et les caractères spéciaux (accents, €) posent problème en CSV sans BOM.

### D2 — Vue unique avec filtres GET
Une seule vue `export_facturation` gère le formulaire (GET) et le téléchargement (POST). Les filtres sont passés en GET pour le formulaire, le POST déclenche la génération. Cela évite de multiplier les vues.

### D3 — Service dédié pour la génération Excel
La logique de génération Excel est dans un service `exports.py` séparé des vues. Le service reçoit un queryset filtré et retourne un `HttpResponse` avec le fichier. Cela permet de réutiliser la logique et de tester indépendamment.

### D4 — Colonnes de l'export
Le fichier contient : N° BDC, Bailleur, Adresse, Ville, Sous-traitant, % ST, Montant HT, Montant ST, Date réalisation, Statut. Le CDT a besoin de toutes ces informations pour le rapprochement facturation.

### D5 — Accès CDT uniquement
L'export contient des montants confidentiels (montant ST, pourcentage). L'accès est restreint au groupe CDT via `@group_required("CDT")`.

## Risks / Trade-offs

- **[Dépendance openpyxl]** → Bibliothèque mature et largement utilisée, risque minimal. Installation via `uv add openpyxl`.
- **[Volume de données]** → 50-150 BDC/mois, l'export en mémoire est suffisant. Pas besoin de streaming.
- **[Filtres date sur date_realisation]** → La date de réalisation n'est renseignée que pour les BDC A_FACTURER et FACTURE. Le filtre période porte sur `date_realisation`, pas `created_at`, car c'est la date pertinente pour la facturation.
