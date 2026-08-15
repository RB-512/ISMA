## Why

Retours de tests utilisateurs (mars 2026) : 5 bugs et améliorations identifiés lors de l'utilisation en production. Le point le plus critique est une erreur 500 lors de la facturation quand la date de prestation est dans le passé, qui peut mener à un passage en "Facturé" non contrôlé si l'utilisateur retente.

## What Changes

- **Fix erreur 500 facturation date passée** : gérer proprement le cas où la date prestation < date actuelle au lieu de crasher. Afficher un message d'erreur clair.
- **Fix incohérence occupation/contact** : ne pas afficher le bloc "Occupant" dans les contacts quand `Occupation = Non renseigné`.
- **Relevé facturation — ajouter la ville** : compléter la colonne Adresse du relevé de facturation avec la ville dans l'export PDF.
- **Fiche chantier ST — ajouter étage et porte** : afficher le numéro d'étage et le numéro de porte sur la fiche chantier sous-traitant.
- **Sidebar — masquer scrollbar verticale** : masquer visuellement la scrollbar tout en gardant le scroll fonctionnel.

## Capabilities

### New Capabilities

_(aucune)_

### Modified Capabilities

- `fiche-detail-bdc`: ne pas afficher le contact occupant quand l'occupation est "Non renseigné"
- `export-facturation`: ajouter la ville dans la colonne Adresse du relevé PDF
- `generation-bdc-terrain`: ajouter étage et porte sur la fiche chantier sous-traitant
- `suivi-realisation`: gérer le cas date prestation passée lors du passage en facturation
- `base-template-ui`: masquer la scrollbar verticale de la sidebar

## Impact

- **Templates** : `bdc/detail.html`, `bdc/fiche_chantier_st.html`, `base.html`
- **Services/Views** : `apps/bdc/views.py` (vue facturation)
- **Exports** : `apps/bdc/releves_export.py` (PDF)
- **CSS** : styles sidebar
- **Aucun changement de modèle**
