## Context

Les parsers `GDHParser` et `ERILIAParser` (`apps/pdf_extraction/`) ont été écrits avec des patterns regex hypothétiques lors du SPEC-001. L'analyse des vrais PDFs modèles via pdfplumber révèle que le texte extrait ne correspond à aucun des patterns actuels. Chaque champ doit être recalibré sur la sortie réelle de pdfplumber.

Sortie pdfplumber réelle du PDF GDH (extrait) :
```
Bon de commande
reprise peinture SDB
suite trx faience
n° 450056 du 09/02/2026
GRAND DELTA HABITAT
Marché n° 026322-CPP-003
...
Habitation n° 000756 de type Type 3, Etage 1, porte 107
...
Occupant actuel : MUSELLA CHRISTIANE (074143/35)
Emetteur : Joseph LONEGRO
...
Total HT 167.85 €
Total TVA 10.00 % 16.79 €
Total TTC 184.64 €
```

Sortie pdfplumber réelle du PDF ERILIA (extrait) :
```
ERILIA
BON DE TRAVAUX
ERILIA N° 2026 20205
Marché n° 2025 356 4 1
ÉMETTEUR ARCQ GWENAEL Tél 0432743295
Programme 1398 LES TERRASSES DE MERCURE
ADRESSE 5 RUE DE LA PETITE VITESSE
84000 AVIGNON
...
TOTAL H.T. 1.071,40
T.V.A. 10,00 % 107,14
TOTAL T.T.C. 1.178,54
...
Édité le
06-02-2026
```

## Goals / Non-Goals

**Goals :**
- Chaque regex matche exactement le texte pdfplumber des PDFs modèles réels
- Tests d'intégration avec les vrais PDFs vérifient les valeurs extraites
- L'interface (dict de sortie) reste identique — aucun changement de contrat

**Non-Goals :**
- Pas de support de nouveaux bailleurs (GDH + ERILIA seulement)
- Pas de refactoring de l'architecture parser (base.py, detector.py inchangés)
- Pas d'extraction des lignes de prestation pour cette itération (complexité table trop élevée — sera un SPEC dédié)
- Pas de modification du modèle `BonDeCommande`

## Decisions

### D1 : Parsing textuel exclusif (pas de tables pdfplumber)

Les tables pdfplumber retournent des structures incohérentes pour ces PDFs (GDH = 2 colonnes mélangées, ERILIA = 1 colonne fusionnée). Toutes les données seront extraites via `extract_text()` et regex sur le texte brut.

**Alternative rejetée** : Parser les tables pdfplumber avec heuristiques adaptatives — trop fragile et spécifique à chaque PDF.

### D2 : Patterns regex spécifiques (pas de patterns génériques)

Chaque champ aura un pattern calibré précisément sur le format observé dans les PDFs modèles, plutôt que des patterns génériques avec alternatives.

Exemples :
- GDH numero_bdc : `r"n°\s+(\d+)\s+du\s+"` au lieu de `r"(?:BDC|BC)\s*n°\s*(\S+)"`
- ERILIA numero_bdc : `r"N°\s+(\d{4}\s+\d{5})"` au lieu de patterns génériques

**Justification** : On connaît exactement les 2 formats. Des patterns trop larges risquent de matcher du bruit.

### D3 : GDH — extraction de l'en-tête multi-lignes

L'en-tête GDH contient le titre, l'objet travaux, le numéro et la date sur les premières lignes :
```
Bon de commande        ← marqueur
reprise peinture SDB   ← objet travaux ligne 1
suite trx faience      ← objet travaux ligne 2
n° 450056 du 09/02/2026  ← numéro + date
```

L'objet travaux sera extrait comme le texte entre "Bon de commande" et la ligne "n° ...".

### D4 : GDH — extraction Habitation en une seule ligne

Le format `Habitation n° 000756 de type Type 3, Etage 1, porte 107` sera parsé avec un seul regex multi-groupes plutôt que 4 regex séparés.

### D5 : ERILIA — extraction page 2 pour la date

La date d'émission ERILIA est sur la page 2 (`Édité le\n06-02-2026`). Le parser concatène déjà toutes les pages dans `texte_p1`, donc le regex `r"Édité le\n(\d{2}-\d{2}-\d{4})"` suffira.

### D6 : Lignes de prestation = liste vide temporairement

L'extraction des lignes de prestation est reportée à un SPEC dédié. Les parsers retourneront `[]` pour `lignes_prestation`. Les tests actuels qui vérifient une liste non-vide seront adaptés.

**Justification** : Le parsing des prestations nécessite une approche spécifique (parsing textuel de blocs multi-lignes dans des cellules fusionnées) qui mérite sa propre itération.

### D7 : Tests d'intégration avec vrais PDFs

Les tests utiliseront les fichiers `docs/Modèle_bdc_GDH.pdf` et `docs/Modèle_bdc_ERILIA.pdf` comme fixtures. Chaque test vérifiera la valeur exacte extraite (pas juste non-vide).

## Risks / Trade-offs

- **Couplage aux PDFs modèles** : Les patterns sont calibrés sur 1 exemplaire par bailleur. D'autres PDFs GDH/ERILIA pourraient avoir des variations. → Mitigation : ajouter des PDFs modèles supplémentaires au fur et à mesure et étendre les patterns si besoin.
- **Lignes de prestation vides** : L'upload crée des BDC sans lignes de prestation pour l'instant. → Mitigation : SPEC dédié planifié. Le modèle `LignePrestation` est déjà en place.
- **Encodage pdfplumber** : Certains caractères (°, accents) peuvent varier selon la version de pdfplumber ou l'encodage du PDF. → Mitigation : patterns avec alternatives pour les caractères spéciaux (`[°o]`).
