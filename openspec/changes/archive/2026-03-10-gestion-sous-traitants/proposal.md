## Why

Actuellement, les sous-traitants sont gérés uniquement via le Django admin. Le CDT et la secrétaire n'ont qu'une vue liste en lecture seule. Pour ajouter, modifier ou désactiver un sous-traitant, il faut passer par l'admin Django — ce qui n'est pas acceptable en production. Il faut une interface CRUD complète intégrée à l'application, avec validation SIRET et adresse.

## What Changes

- Ajout des champs `siret`, `adresse`, `code_postal`, `ville` au modèle `SousTraitant`
- Interface CRUD complète (créer, modifier, désactiver/réactiver) accessible depuis la sidebar existante
- Validation du format SIRET (14 chiffres, algorithme de Luhn)
- Vue liste enrichie avec recherche, tri, et affichage des nouveaux champs
- Bouton d'action rapide sur chaque ligne (modifier, désactiver)
- Protection : un sous-traitant lié à des BDC ne peut pas être supprimé (désactivation uniquement)

## Capabilities

### New Capabilities
- `gestion-sous-traitants`: CRUD complet des sous-traitants (créer, lire, modifier, désactiver/réactiver) avec validation SIRET et champs adresse

### Modified Capabilities

## Impact

- **Modèle** : `apps/sous_traitants/models.py` — ajout champs siret, adresse, code_postal, ville + migration
- **Vues** : `apps/sous_traitants/views.py` — remplacer ListView par vues CRUD complètes
- **URLs** : `apps/sous_traitants/urls.py` — nouvelles routes creer/modifier/desactiver/reactiver
- **Templates** : `templates/sous_traitants/` — refonte list.html + formulaires
- **Forms** : nouveau `apps/sous_traitants/forms.py` — formulaires avec validation SIRET
- **Tests** : nouveau `tests/test_sous_traitants/` — tests forms + views + RBAC
