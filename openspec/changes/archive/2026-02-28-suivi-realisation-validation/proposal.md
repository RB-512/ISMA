## Why

Les étapes 3-4 du workflow (attribution + envoi terrain) sont implémentées, mais le CDT n'a aucun moyen de marquer un BDC comme réalisé ni de valider le passage en facturation. Sans cette fonctionnalité, le cycle de vie du BDC s'arrête à "En cours" et le rapprochement hebdomadaire BDC attribués vs réalisations reste sur papier.

## What Changes

- Ajouter une vue de validation pour le CDT : marquer un BDC EN_COURS comme réalisé (→ A_FACTURER)
- Ajouter une vue de passage en facturation : valider un BDC A_FACTURER (→ FACTURE)
- Ajouter un champ `date_realisation` sur le modèle BDC pour tracer quand les travaux ont été déclarés terminés
- Créer un écran de recoupement par sous-traitant : liste des BDC attribués à un ST donné, groupés par statut, pour faciliter le rapprochement hebdomadaire
- Ajouter les boutons CDT sur la fiche détail pour les transitions EN_COURS → A_FACTURER et A_FACTURER → FACTURE
- Tracer les actions VALIDATION et FACTURATION dans l'historique

## Capabilities

### New Capabilities
- `suivi-realisation`: Validation de la réalisation par le CDT (EN_COURS → A_FACTURER), passage en facturation (A_FACTURER → FACTURE), traçabilité des actions
- `recoupement-st`: Écran de rapprochement par sous-traitant pour le CDT — liste des BDC attribués à un ST, filtrables par statut, pour le recoupement hebdomadaire

### Modified Capabilities
- `fiche-detail-bdc`: Ajout des boutons CDT "Valider réalisation" (EN_COURS → A_FACTURER) et "Passer en facturation" (A_FACTURER → FACTURE)

## Impact

- `apps/bdc/models.py` : ajout champ `date_realisation`
- `apps/bdc/services.py` : fonctions `valider_realisation()` et `valider_facturation()`
- `apps/bdc/views.py` : vues CDT pour validation et facturation + vue recoupement
- `apps/bdc/urls.py` : nouvelles routes
- `templates/bdc/detail.html` : boutons CDT
- `templates/bdc/recoupement.html` : nouvel écran
- Migration pour le nouveau champ
