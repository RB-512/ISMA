## Why

Le CDT ne peut pas encore attribuer un BDC à un sous-traitant depuis l'application. Actuellement, les BDC passent de "À faire" à "En cours" via un simple bouton sur la fiche détail, sans aucune sélection de ST ni fixation de montant. L'attribution est l'étape 3 du workflow PRD (section 5.3) et constitue le pivot entre la préparation secrétaire et la réalisation terrain.

## What Changes

- Ajouter une **page d'attribution** : le CDT sélectionne un ST actif, fixe le pourcentage/montant ST, et valide
- Le BDC passe automatiquement en statut **En cours** après attribution
- Envoyer une **notification SMS** au ST avec les infos terrain (adresse, occupation, accès, travaux) — sans les prix
- Permettre la **réattribution** : changer de ST tant que les travaux n'ont pas commencé (statut En cours), avec traçabilité
- Ajouter une vue **liste des ST** avec template (la vue existe mais le template manque)
- La fiche détail affiche un **bouton "Attribuer"** quand le BDC est en statut À_FAIRE et l'utilisateur est CDT

## Capabilities

### New Capabilities
- `attribution-bdc`: Attribution d'un BDC à un sous-traitant par le CDT, incluant sélection du ST, montant ST, notification SMS, et réattribution

### Modified Capabilities
- `fiche-detail-bdc`: Ajout du bouton "Attribuer" conditionnel (statut À_FAIRE + rôle CDT) et affichage des infos d'attribution (ST, montant ST)

## Impact

- `bdc-peinture/apps/bdc/views.py` : nouvelles vues `attribuer_bdc`, `reattribuer_bdc`
- `bdc-peinture/apps/bdc/urls.py` : nouvelles routes `<int:pk>/attribuer/`, `<int:pk>/reattribuer/`
- `bdc-peinture/apps/bdc/forms.py` : nouveau `AttributionForm`
- `bdc-peinture/apps/bdc/services.py` : nouvelle fonction `attribuer_st()` avec logique métier
- `bdc-peinture/templates/bdc/attribuer.html` : nouveau template
- `bdc-peinture/templates/bdc/detail.html` : bouton "Attribuer" conditionnel
- `bdc-peinture/templates/sous_traitants/list.html` : nouveau template pour la liste ST
- `bdc-peinture/apps/bdc/notifications.py` : nouveau module pour l'envoi SMS (stub en V1, pas d'intégration SMS réelle)
- Dépendance éventuelle : bibliothèque SMS (hors scope V1, on prépare l'interface)
