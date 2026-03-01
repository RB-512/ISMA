## Why

La vue `controle_bdc` tente le changement de statut même quand le formulaire est invalide, et remplace toujours le formulaire lié (portant les erreurs de `clean()`) par un formulaire vierge — rendant toute erreur de validation de champ invisible pour l'utilisateur. Concrètement, l'utilisateur peut passer un BDC en "À attribuer" sans avoir rempli les champs obligatoires (occupation, type_acces, rdv_date), car les erreurs de la couche formulaire sont silencieusement perdues.

## What Changes

- **Gating de la transition sur `form.is_valid()`** : `changer_statut()` n'est appelé que si le formulaire est valide.
- **Préservation du formulaire lié après échec de validation** : le formulaire avec ses erreurs est conservé pour le re-rendu, au lieu d'être remplacé par un formulaire vierge.
- **Affichage des erreurs de champ** dans `controle.html` : les erreurs `form_edition.field.errors` sont rendues visible à côté de chaque champ.

## Capabilities

### New Capabilities
*(aucune — correction d'un bug existant)*

### Modified Capabilities
- `controle-bdc-form`: Le formulaire de contrôle doit afficher toutes les erreurs de validation de champ et bloquer la transition si le formulaire est invalide.

## Impact

- `apps/bdc/views.py` — fonction `controle_bdc` (~lignes 937-1000) : réorganisation du flux POST
- `templates/bdc/controle.html` — ajout des blocs d'erreurs sur les champs du formulaire
- `tests/test_bdc/test_controle.py` — nouveaux tests de régression vérifiant que les erreurs de formulaire sont bien affichées et que la transition est bloquée
