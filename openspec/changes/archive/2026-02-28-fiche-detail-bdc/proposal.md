## Why

La fiche détail BDC actuelle (`detail.html`) affiche les données extraites du PDF (localisation, travaux, prestations) mais il manque des sections essentielles pour le workflow quotidien : les contacts (occupant et émetteur bailleur), les champs manuels éditables (occupation, modalité d'accès, RDV, notes), et les boutons d'action pour changer le statut. La secrétaire ne peut pas compléter le BDC ni le faire avancer sans retourner à l'admin Django.

## What Changes

- Ajouter une section **Contacts** affichant l'occupant (nom, tél, email) et l'émetteur bailleur (nom, tél)
- Ajouter un **formulaire d'édition inline** pour les champs manuels : occupation (vacant/occupé), modalité d'accès, RDV (pris + date), notes
- Ajouter des **boutons d'action de statut** : afficher les transitions autorisées depuis le statut courant et permettre le changement en un clic (POST)
- Ajouter une vue POST `modifier_bdc` pour sauvegarder les champs manuels
- Ajouter une vue POST `changer_statut_bdc` pour les transitions de statut
- Enrichir la section **Historique** avec les détails JSON (ancien/nouveau statut)
- Afficher le **sous-traitant** attribué quand il existe

## Capabilities

### New Capabilities
- `fiche-detail-bdc`: Fiche de détail complète du BDC avec contacts, édition inline des champs manuels, actions de statut, et informations sous-traitant

### Modified Capabilities

## Impact

- `bdc-peinture/apps/bdc/views.py` : ajout de 2 vues (`modifier_bdc`, `changer_statut_bdc`), enrichissement de `detail_bdc`
- `bdc-peinture/apps/bdc/urls.py` : 2 nouvelles routes
- `bdc-peinture/apps/bdc/forms.py` : nouveau formulaire `BDCEditionForm` (sous-ensemble de champs manuels)
- `bdc-peinture/templates/bdc/detail.html` : refonte du template (contacts, formulaire, boutons statut, sous-traitant)
- `bdc-peinture/apps/bdc/services.py` : pas de modification (logique existante réutilisée)
- Tests : nouveaux tests unitaires pour les vues POST et le formulaire
