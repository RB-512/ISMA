# Design — Relevé de facturation sous-traitant

**Date :** 2026-03-07
**Statut :** Validé

---

## Problème

Le CDT gère ~10 sous-traitants avec des périodicités de facturation variables (hebdomadaire, bimensuelle, mensuelle, ponctuelle). Aujourd'hui, pour identifier les BDC réalisés par un ST depuis sa dernière facturation, le CDT consulte ses SMS ou la dernière facture papier. Risque principal : double facturation d'un BDC.

## Solution

Un modèle **ReleveFacturation** qui regroupe les BDC réalisés par un ST depuis le dernier relevé validé. Workflow brouillon → validé avec verrouillage anti-doublon. Génération PDF (pour le ST) et Excel (pour le CDT).

---

## Modèle de données

### ReleveFacturation

| Champ | Type | Description |
|-------|------|-------------|
| `numero` | PositiveIntegerField | Auto-incrémenté par ST (relevé n°1, 2, 3...) |
| `sous_traitant` | FK → SousTraitant | Le ST concerné |
| `statut` | CharField | BROUILLON / VALIDE |
| `bdc` | M2M → BonDeCommande | Les BDC inclus dans ce relevé |
| `notes` | TextField (blank) | Notes libres du CDT |
| `cree_par` | FK → User | Le CDT qui a créé le relevé |
| `date_creation` | DateTimeField (auto) | Date de création |
| `date_validation` | DateTimeField (null) | Date de validation |

### Propriétés calculées

- `montant_total` : somme des `montant_st` des BDC rattachés
- `nb_bdc` : nombre de BDC rattachés
- `periode_debut` : `date_realisation` min des BDC inclus
- `periode_fin` : `date_realisation` max des BDC inclus

### Contraintes

- Un BDC ne peut être rattaché qu'à un seul relevé validé (contrainte applicative dans le service)
- Un BDC en brouillon peut être retiré
- Le numéro est auto-incrémenté par ST (max(numero) + 1 pour ce ST)

---

## Parcours utilisateur

### Créer un relevé

1. Le CDT va sur la page **Recoupement** (existante)
2. Sur la ligne du ST, il clique **"Nouveau relevé"**
3. L'appli récupère automatiquement les BDC :
   - Attribués à ce ST
   - En statut `A_FACTURER` ou `FACTURE`
   - Non rattachés à un relevé validé existant
4. Le relevé est créé en **BROUILLON** avec ces BDC pré-sélectionnés
5. Le CDT voit : liste des BDC, montant ST de chacun, montant total, période couverte

### Modifier le brouillon

6. Le CDT peut **retirer** un BDC du relevé (case à décocher)
7. Il peut ajouter des **notes** libres
8. Le montant total se recalcule (HTMX)

### Valider

9. Le CDT clique **"Valider le relevé"**
10. Les BDC sont verrouillés (ne pourront plus apparaître dans un autre relevé)
11. Le statut passe à VALIDÉ, la date de validation est enregistrée

### Générer les documents

12. **PDF** (pour le ST) : en-tête avec nom ST + numéro relevé + période, tableau des BDC (n° BDC, adresse, montant ST), total en bas
13. **Excel** (pour le CDT) : mêmes colonnes, pour usage interne
14. Documents disponibles en brouillon et après validation

### Historique

15. Sur la page Recoupement, un lien vers l'historique des relevés du ST
16. Liste : n°, date validation, nb BDC, montant total, statut, liens téléchargement

---

## Intégration UI

### Pages existantes modifiées

- **Recoupement (`recoupement_liste`)** : ajout d'un bouton "Nouveau relevé" par ligne ST + lien "Historique relevés"

### Nouvelles pages

- **Création/édition relevé** : formulaire avec liste BDC cochés, notes, montant total, boutons Valider / PDF / Excel
- **Historique relevés d'un ST** : tableau des relevés passés avec actions

### Aucune modification sur

- Le workflow BDC (statuts inchangés)
- Les statuts existants (A_TRAITER → ... → FACTURE)
- Le modèle BonDeCommande (pas de nouveau champ)

---

## Règles métier

- Seul le CDT peut créer/valider un relevé
- Un relevé ne peut contenir que des BDC du même ST
- Un BDC ne peut être dans qu'un seul relevé validé (anti-doublon)
- Les BDC éligibles : statut A_FACTURER ou FACTURE, attribués au ST, non rattachés à un relevé validé
- Le montant affiché est toujours le `montant_st` (jamais le montant bailleur)
- Le PDF pour le ST ne contient que : n° BDC, adresse, montant ST, total

## Hors périmètre (V2+)

- Génération en lot (tous les ST en un clic)
- Validation en lot
- Envoi automatique du PDF par email au ST
