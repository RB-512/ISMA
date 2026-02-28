## Context

Les parsers GDH et ERILIA extraient actuellement toutes les métadonnées d'un BDC (numéro, adresse, montants, etc.) mais retournent `lignes_prestation: []`. Le modèle `LignePrestation` existe déjà avec les champs : `designation`, `quantite`, `unite`, `prix_unitaire`, `montant`, `ordre`. La vue `creer_bdc` consomme déjà `lignes_prestation` depuis la session pour créer les objets en base.

**Données réelles extraites par pdfplumber :**

GDH — Table page 1, Row 2 = en-tête colonnes, Row 3 = lignes (cellule unique) :
```
Row 2: ['P.U.H.T (€) Quantité Montant HT (€) TVA', None]
Row 3: ['M-P : préparation et mis (PS1402) 11.19 15.00 (m²) 167.85 10.00%\nM-P : préparation et mise en peinture', None]
```

ERILIA — Table 1, page 1, Row 0 = en-tête, Row 1 = lignes (cellule unique multi-lignes) :
```
Row 0: ['ARTICLE DÉSIGNATION UNITÉ QUANTITÉ PRIX UNITAIRE H.T. TOTAL T.T.C.']
Row 1: ['PP4-31 Peinture finition A sur murs, plafond, FOR 1,00 180,27 198,30\nboiseries et métalleries - WC\nEDL : ...\nPP4-33 Peinture finition A sur murs, plafond, FOR 1,00 313,10 344,41\nboiseries et métalleries - cuisine\nEDL : ...\nPP4-43 Peinture finition A sur plafonds - FOR 1,00 578,03 635,83\nlogement complet T3\nEDL : ...']
```

## Goals / Non-Goals

**Goals :**
- Extraire les lignes de prestation depuis les tables PDF réelles (GDH et ERILIA)
- Retourner une `list[dict]` avec les champs compatibles `LignePrestation` : `code`, `designation`, `unite`, `quantite`, `prix_unitaire`, `montant_ht`
- Gérer les lignes de description multi-lignes (désignation sur 2+ lignes)
- Tests unitaires mockés et tests d'intégration sur les vrais PDFs

**Non-Goals :**
- Pas de modification du modèle `LignePrestation` (il existe déjà)
- Pas de modification de la vue `creer_bdc` (elle consomme déjà les lignes)
- Pas de parsing des lignes EDL (commentaires) — elles sont ignorées
- Pas de gestion de PDFs avec un nombre variable de pages de prestations (un seul bloc par PDF modèle)

## Decisions

### D1 : Extraction depuis les tables pdfplumber (pas le texte brut)

Les lignes de prestation dans les deux formats sont structurées dans des tableaux PDF. L'extraction par table (`extract_tables()`) donne une cellule contenant toutes les lignes, plus fiable que le texte brut qui mélange colonnes et retours à la ligne.

**Alternative rejetée** : regex sur `extract_text()` — les colonnes numériques se chevauchent et les descriptions multi-lignes rendent le parsing fragile.

### D2 : Regex par ligne dans la cellule de table

Chaque cellule contient N lignes de prestation concaténées avec `\n`. On split par `\n` et on applique un regex adapté à chaque format pour identifier les lignes-données (vs lignes de continuation de désignation ou commentaires EDL).

**GDH** — pattern par ligne :
```
M-P : préparation et mis (PS1402) 11.19 15.00 (m²) 167.85 10.00%
```
→ regex : `^(.+?)\s+(\d+[\d.]*)\s+(\d+[\d.]*)\s*\(([^)]+)\)\s+(\d+[\d.]*)\s+[\d.]+%$`
  - group 1 = désignation (ex: `M-P : préparation et mis (PS1402)`)
  - group 2 = prix unitaire HT
  - group 3 = quantité
  - group 4 = unité
  - group 5 = montant HT

**ERILIA** — pattern par ligne :
```
PP4-31 Peinture finition A sur murs, plafond, FOR 1,00 180,27 198,30
```
→ regex : `^(\S+)\s+(.+?)\s+(FOR|M2|ML|U|ENS|H)\s+([\d,]+)\s+([\d.,]+)\s+([\d.,]+)$`
  - group 1 = code article
  - group 2 = désignation (tronquée — la suite est sur la ligne suivante)
  - group 3 = unité
  - group 4 = quantité
  - group 5 = prix unitaire HT
  - group 6 = montant TTC (on calcule le HT depuis le prix_unitaire × quantité)

### D3 : Lignes de continuation concaténées à la désignation

Pour ERILIA, la désignation est coupée en fin de première ligne. Les lignes suivantes qui ne matchent pas le pattern d'une nouvelle prestation sont concaténées à la désignation de la ligne précédente (sauf les lignes `EDL :` qui sont ignorées).

Pour GDH, la ligne suivante `M-P : préparation et mise en peinture` est la description complète — elle est concaténée.

### D4 : Montant HT pour ERILIA calculé depuis prix_unitaire × quantité

La table ERILIA affiche `PRIX UNITAIRE H.T.` et `TOTAL T.T.C.` mais pas directement le total HT par ligne. Le montant HT est le prix_unitaire × quantité (tous deux HT). On vérifie la cohérence via `TOTAL H.T.` global.

### D5 : Champ `code` ajouté au dict retourné mais optionnel

ERILIA a un code article (`PP4-31`), GDH n'en a pas. Le dict retourné inclut `code` (vide pour GDH). Le modèle `LignePrestation` n'a pas de champ `code` — il est ignoré lors de la création en base, mais disponible pour affichage ou évolution future.

## Risks / Trade-offs

- **[Fragile si format PDF change]** → Les regex sont calibrés sur les PDFs modèles. Si ERILIA ou GDH change son format, les lignes ne seront pas extraites (fallback : `[]`). Mitigation : les tests d'intégration détecteront les régressions.
- **[Cellule unique pour toutes les lignes]** → pdfplumber fusionne toutes les lignes en une seule cellule. Si le PDF a des bordures de cellules entre chaque ligne, la structure changera. Mitigation : on parse `\n`-separated text dans la cellule.
- **[Montant HT ERILIA calculé]** → Le total HT par ligne n'est pas directement dans le PDF. Risque d'arrondi. Mitigation : on utilise `Decimal` et on quantize à 2 décimales.
