## Context

L'attribution BDC (SPEC-006) est faite. Le CDT a besoin d'envoyer au ST une version terrain sans prix. Le modèle `BonDeCommande` a un `pdf_original` (FileField) et un `bailleur` (FK avec code GDH ou ERILIA). Les dépendances `pymupdf` (extraction/manipulation PDF) et `weasyprint` (HTML→PDF) sont déjà installées. Le BDC a toutes les données nécessaires (adresse, travaux, occupant, prestations sans prix).

## Goals / Non-Goals

**Goals:**
- Extraire la page 2 du PDF GDH comme BDC terrain (c'est déjà le bon d'intervention sans prix)
- Générer un PDF terrain sans prix pour ERILIA via un template HTML + WeasyPrint
- Stocker le PDF terrain sur le BDC pour téléchargement ultérieur
- Permettre au CDT (et à la secrétaire) de télécharger le BDC terrain depuis la fiche détail
- Générer automatiquement le PDF terrain lors de l'attribution

**Non-Goals:**
- Pas d'envoi automatique par SMS/email du PDF terrain au ST (V2)
- Pas de visualisation inline du PDF dans l'application (un simple téléchargement suffit)
- Pas de personnalisation du template terrain par bailleur au-delà de GDH/ERILIA
- Pas de régénération manuelle (si les données changent, la réattribution régénère)

## Decisions

### D1 : Module dédié `terrain.py` dans apps/bdc
La logique de génération du PDF terrain est dans un nouveau module `apps/bdc/terrain.py` avec une fonction principale `generer_pdf_terrain(bdc)` qui dispatche vers la bonne stratégie selon le bailleur.
**Raison** : Séparation claire. Les services métier (services.py) appellent terrain.py, pas l'inverse.
**Alternative rejetée** : Tout dans services.py — trop gros, mélange logique métier et génération PDF.

### D2 : PyMuPDF pour l'extraction de page GDH
On utilise `fitz` (pymupdf) pour extraire la page 2 du PDF original et la sauvegarder comme nouveau PDF.
**Raison** : PyMuPDF est déjà en dépendance, rapide et fiable pour la manipulation de pages PDF.
**Alternative rejetée** : pdfplumber — bon pour l'extraction texte, pas pour la manipulation de pages.

### D3 : WeasyPrint + template HTML pour ERILIA
On crée un template Django `terrain_erilia.html` avec les données du BDC (adresse, travaux, prestations SANS prix) et on le convertit en PDF via WeasyPrint.
**Raison** : WeasyPrint est déjà en dépendance. Un template HTML est facile à maintenir et permet un rendu propre.
**Alternative rejetée** : Manipuler le PDF ERILIA original pour masquer les prix — fragile, dépend de la position exacte du texte.

### D4 : Champ `pdf_terrain` FileField sur BonDeCommande
Le PDF terrain est stocké comme fichier media, attaché au BDC via un nouveau FileField `pdf_terrain`.
**Raison** : Cohérent avec `pdf_original`. Permet le téléchargement direct sans regénération.

### D5 : Génération automatique à l'attribution
Le PDF terrain est généré automatiquement quand `attribuer_st()` est appelé (et lors de `reattribuer_st()`). La vue d'attribution n'a pas besoin de s'en soucier.
**Raison** : Le BDC terrain est toujours nécessaire après attribution. Automatiser évite l'oubli.

### D6 : Vue de téléchargement séparée
Une vue `telecharger_terrain(pk)` sert le fichier PDF en téléchargement. Accessible à tout utilisateur authentifié.
**Raison** : Simple, pas besoin de restreindre l'accès au PDF terrain (pas de prix dedans).

## Risks / Trade-offs

- [WeasyPrint lent] La génération PDF ERILIA peut prendre 1-2s → Acceptable pour le volume (50-150 BDC/mois). Pas de queue asynchrone nécessaire.
- [PDF GDH sans page 2] Si le PDF original n'a qu'une page → On retourne une erreur explicite. En pratique tous les PDF GDH ont 2 pages.
- [Template ERILIA approximatif] Le rendu ne sera pas identique au PDF original → OK, l'objectif est d'avoir les bonnes infos sans prix, pas un fac-similé.
- [Migration] Nouveau champ FileField → Migration légère, nullable, pas de data migration nécessaire.
