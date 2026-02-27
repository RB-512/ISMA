## Context

Le projet dispose déjà de stubs `GDHParser`, `ERILIAParser` et `detecter_parser()` dans `apps/pdf_extraction/`. Les modèles `BonDeCommande` (avec `pdf_original`) et `LignePrestation` sont en place. Il reste à implémenter les parsers, le flow d'upload et le formulaire de création.

Deux formats PDF entrants :
- **GDH** : 2 pages. Page 1 = récapitulatif avec prix. Page 2 = BDC terrain sans prix (déjà prêt à imprimer). L'extraction cible les deux pages (données admin de la page 1, BDC terrain de la page 2).
- **ERILIA** : 1 page. Toutes les données + prix. Le BDC terrain sera généré en SPEC-003.

Acteurs : uniquement la **secrétaire** peut uploader et créer des BDC.

## Goals / Non-Goals

**Goals:**
- Implémenter `GDHParser.extraire()` et `ERILIAParser.extraire()` retournant un dict normalisé
- Implémenter `detecter_parser()` via pattern matching sur la première page
- Vue d'upload (POST) → extraction → redirection vers formulaire pré-rempli
- Formulaire de création BDC avec validation (doublon, occupation)
- Stockage du PDF original et log `HistoriqueAction.CREATION`

**Non-Goals:**
- OCR (les PDFs GDH/ERILIA sont machine-readable)
- Génération du BDC terrain ERILIA (SPEC-003)
- Extraction parfaite à 100% (champs manquants = blancs → complétés manuellement)
- Multi-upload ou import CSV

## Decisions

### D1 — pdfplumber comme extracteur principal

**Choix** : pdfplumber pour l'extraction de texte et tables, PyMuPDF en fallback si pdfplumber retourne vide.

**Rationale** : pdfplumber excelle sur les PDFs avec tables structurées (cas GDH). PyMuPDF est plus rapide pour l'extraction brute de texte (cas ERILIA). Les deux sont déjà dans pyproject.toml.

**Alternatif écarté** : pdfminer seul — moins de support tables.

### D2 — Détection par pattern textuel sur la page 1

**Choix** : `detecter_parser()` lit le texte de la page 1 et cherche des marqueurs uniques (ex: `"GRAND DELTA HABITAT"` → GDH, `"ERILIA"` → ERILIA).

**Rationale** : Simple, rapide, fiable tant que les en-têtes PDF ne changent pas. Pas besoin de ML.

**Alternatif écarté** : Détection par métadonnées PDF — peu fiable (métadonnées souvent vides).

### D3 — Flow en 2 étapes (upload séparé du formulaire)

**Choix** : POST sur `/bdc/upload/` → extraction → GET sur `/bdc/nouveau/?source=<session_key>` avec données en session Django.

**Rationale** : Sépare la responsabilité d'extraction de la responsabilité de validation. Permet de retenter le formulaire sans re-uploader. La session Django est déjà configurée.

**Alternatif écarté** : Upload + formulaire en une seule page (HTMX swap) — complexifie la gestion d'erreur d'extraction.

### D4 — Données extraites en session (pas de modèle intermédiaire)

**Choix** : Le dict extrait est stocké en session Django (`request.session["bdc_extrait"]`) entre l'upload et le formulaire.

**Rationale** : Pas besoin d'un modèle `BDCBrouillon` — la session suffit pour 1 utilisateur à la fois. Si la session expire, l'utilisateur re-uploade.

### D5 — Statut initial selon occupation

**Choix** : Si `occupation` est renseigné dans le formulaire → statut `A_FAIRE`. Sinon → `A_TRAITER`.

**Rationale** : Respecte la règle métier existante dans `changer_statut()` (BDCIncomplet). La secrétaire peut directement passer en À_FAIRE si elle connaît l'occupation.

### D6 — Doublon bloquant au submit du formulaire

**Choix** : Validation côté `BonDeCommandeForm.clean_numero_bdc()` — si un BDC avec ce numéro existe déjà, `ValidationError` bloquante.

**Rationale** : Le numéro BDC est unique en base (contrainte `unique=True`). La validation explicite donne un message clair ("BDC 12345 déjà enregistré").

## Risks / Trade-offs

- **Fragilité regex** → Si GDH/ERILIA modifient leur format PDF, l'extraction plante silencieusement (champs vides). Mitigation : tests avec PDF fixtures réels + champs non-critiques laissés vides plutôt que d'écraser.
- **Données en session** → Si le serveur redémarre entre upload et soumission, la session est perdue. Mitigation : message d'erreur explicite ("Session expirée, veuillez ré-uploader").
- **PDF malformé** → pdfplumber peut lever une exception sur un PDF corrompu. Mitigation : try/except dans la vue upload, message d'erreur utilisateur.
- **GDH page 2** → Si le PDF GDH n'a qu'une page, l'extraction page 2 retourne vide. Mitigation : extraction gracieuse (None si page absente).

## Migration Plan

Pas de migration de données requise. Les stubs existants sont remplacés (même signatures). Les migrations Django ne sont pas impactées.
