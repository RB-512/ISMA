## Why

Quand un sous-traitant recoit un email d'attribution, l'objet ne contient que le numero BDC. Quand le CDT envoie plusieurs attributions, le ST ne peut pas distinguer rapidement les mails dans sa boite de reception. Ajouter le nom du ST dans l'objet permet une identification immediate.

## What Changes

- Ajouter le nom du sous-traitant dans l'objet de l'email d'attribution (defaut : `BDC {numero_bdc} — Attribution — {nom_st}`)
- Ajouter la variable `{nom_st}` dans les variables de substitution du template personnalisable
- Mettre a jour l'aide des variables disponibles dans la page Configuration > Email ST

## Capabilities

### New Capabilities

_(aucune)_

### Modified Capabilities

- `notifications-email`: ajouter `{nom_st}` dans les variables de substitution et dans l'objet par defaut

## Impact

- `apps/notifications/email.py` : ajout variable `nom_st`, modification objet par defaut
- `templates/accounts/config_bailleur.html` : ajout `{nom_st}` dans la liste des variables disponibles
