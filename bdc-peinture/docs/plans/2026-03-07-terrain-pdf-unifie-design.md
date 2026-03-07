# Processus unifie PDF terrain

## Objectif

Remplacer les deux strategies actuelles (GDH: extraction page 2 / ERILIA: WeasyPrint)
par un processus unique : generer le PDF terrain avec PyMuPDF depuis les donnees en base.

## Approche

Approche C — Generation depuis la base de donnees avec PyMuPDF.
Un seul chemin de code, zero regex, zero dependance WeasyPrint pour le terrain,
zero maintenance par bailleur.

## Contenu du PDF terrain

### En-tete
Nom du bailleur en gros + numero BDC.
Ex: "GRAND DELTA HABITAT — BDC Terrain N 450056"

### Sections
1. Localisation : adresse, residence, logement, occupation, acces
2. Travaux : objet, delai d'execution
3. Contact occupant : nom + telephone
4. Prestations : designation, quantite, unite (SANS PRIX)
5. Mention "DOCUMENT TERRAIN — SANS PRIX"

### Exclus
- Montants (HT, TVA, TTC), prix unitaires
- Contact emetteur (tel, email)
- Logos

## Fichiers impactes

- `apps/bdc/terrain.py` : reecrit avec une seule fonction PyMuPDF
- `tests/test_bdc/test_terrain.py` : tests adaptes
- `templates/bdc/terrain_erilia.html` : supprime

## Impact

- Pas de migration
- Pas de changement de modele
- Supprime la dependance WeasyPrint pour la generation terrain
