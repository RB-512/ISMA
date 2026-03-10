# Bibliothèque de prix & attribution par forfait

**Date** : 2026-03-10

## Contexte

Le CDT dispose d'une grille de prix forfaitaires négociés avec les sous-traitants. Lors de l'attribution d'un BDC, il veut pouvoir choisir entre :
- Un pourcentage du montant HT (mode actuel)
- Un devis composé de lignes issues de sa bibliothèque de prix

Les deux modes sont mutuellement exclusifs.

## Modèle `PrixForfaitaire`

| Champ | Type | Exemple |
|-------|------|---------|
| `reference` | CharField unique | "PEINT-T2" |
| `designation` | CharField | "Peinture logement T2" |
| `unite` | CharField | "u", "m²", "ml", "forfait" |
| `prix_unitaire` | DecimalField | 900.00 |
| `actif` | BooleanField | true |

Grille universelle (pas liée à un sous-traitant).

## Page "Bibliothèque" (sidebar)

- Accessible au CDT (et admin)
- Tableau CRUD : Référence, Désignation, Unité, PU
- Actions : ajouter, modifier, supprimer
- Modification inline HTMX
- Item sidebar : "Bibliothèque"

## Modèle `LigneForfaitAttribution`

Lignes du "devis ST" associées à un BDC :

| Champ | Type |
|-------|------|
| `bon_de_commande` | FK → BonDeCommande |
| `prix_forfaitaire` | FK → PrixForfaitaire |
| `quantite` | DecimalField |
| `prix_unitaire` | DecimalField (pré-rempli depuis bibliothèque, modifiable) |
| `montant` | DecimalField (calculé : qté × PU) |

## Attribution : choix du mode

Toggle Alpine.js entre deux modes exclusifs :

- **Mode "Pourcentage"** (défaut) : champ pourcentage → `montant_st = montant_ht × %`
- **Mode "Forfait"** : interface d'ajout de lignes
  - Dropdown pour choisir un prix de la bibliothèque
  - Champ quantité
  - PU pré-rempli, modifiable
  - Bouton "+" pour ajouter la ligne
  - Tableau des lignes ajoutées avec total en bas
  - `montant_st` = somme des lignes

## Stockage sur le BDC

- `mode_attribution` : CharField ("pourcentage" / "forfait")
- `montant_st` et `pourcentage_st` toujours remplis (pourcentage calculé en inverse en mode forfait)
- Les `LigneForfaitAttribution` ne sont créées qu'en mode forfait

## Hors périmètre

- Pas de mix pourcentage + forfait sur un même BDC
- Pas de prix par sous-traitant
