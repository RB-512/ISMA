## Why

Le mail d'attribution envoye au sous-traitant manque d'informations de localisation precises (etage, porte) alors que ces donnees existent sur le BDC. Par ailleurs, la fiche chantier PDF est aujourd'hui toujours jointe automatiquement sans que le CDT puisse en decider — certains cas necessitent de ne pas la transmettre.

## What Changes

- **Corps du mail** : ajouter les variables `{etage}` et `{porte}` dans le template d'email d'attribution (et de reattribution)
- **Toggle "Joindre le BDC"** : ajouter un toggle dans la barre d'onglets du viewer PDF (page attribution split-screen) qui :
  - Par defaut : actif (fiche chantier jointe, bouton "Vue sous-traitant" visible)
  - Quand desactive : fiche chantier non jointe, bouton "Vue sous-traitant" masque, vue bascule automatiquement sur "PDF original"
  - Transmet la decision via un champ hidden dans le formulaire d'attribution

## Capabilities

### New Capabilities

- `toggle-joindre-bdc` : toggle UI dans le viewer PDF controlant la piece jointe et la visibilite du bouton "Vue sous-traitant"

### Modified Capabilities

- `email-attribution` : ajout des variables etage/porte dans le corps du mail et prise en compte du choix de joindre ou non la fiche chantier

## Impact

- `templates/bdc/attribution_split.html` : ajout du toggle dans la barre d'onglets
- `apps/notifications/email.py` : ajout variables etage/porte + parametre `joindre_pdf`
- `apps/bdc/services.py` : passage du parametre `joindre_pdf` lors de l'appel a la notification
- `apps/bdc/views.py` : lecture du champ `joindre_bdc` dans le POST de l'attribution
- `apps/bdc/forms.py` : ajout du champ `joindre_bdc` (BooleanField, initial=True)
