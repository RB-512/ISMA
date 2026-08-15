## Why

Revue de code globale du projet BDC Peinture ayant identifie 22 issues (securite, integrite des donnees, robustesse). Les plus critiques : mot de passe prod visible dans le HTML de la page de login, RBAC manquant sur les vues CDT et gestion utilisateurs (une Secretaire peut attribuer des BDC ou creer des comptes admin), et absence de transactions atomiques sur les operations multi-ecritures.

## What Changes

- Supprimer/masquer les credentials prod exposes dans `login.html` et externaliser ceux de `e2e/helpers.py`
- Ajouter `@group_required('CDT')` sur toutes les vues de workflow (attribution, validation, facturation) et de gestion utilisateurs
- Envelopper les operations multi-ecritures dans `transaction.atomic()` (services.py, creer_bdc)
- Corriger les notifications pour ne jamais bloquer le workflow (try/except manquants dans email et SMS)
- Corriger `export_facturation` qui ignore les filtres en POST
- Remplacer `mark_safe()` par `format_html()` pour eviter XSS
- Corriger les filtres date sur DateTimeField (`date__lte`/`date__gte`)
- Ajouter des guards de validation (parse forfait, sidebar form errors, modifier_bdc statut, erilia parser)
- Ajouter contrainte unique sur `ReleveFacturation.numero` par sous-traitant
- Corriger la mutation d'etat sur GET dans `sidebar_checklist`
- Ajouter limite taille upload et auth sur media en mode LAN

## Capabilities

### New Capabilities

_(aucune)_

### Modified Capabilities

- `authentification-roles`: ajouter `@group_required('CDT')` sur les vues de workflow et de gestion utilisateurs
- `attribution-bdc`: transactions atomiques dans `attribuer_st` et `reattribuer_st`, try/except notifications
- `suivi-realisation`: transactions atomiques dans `valider_realisation` et `valider_facturation`
- `notifications-email`: try/except dans `envoyer_email_attribution`, guard `format_map` sur templates admin
- `notifications-sms`: try/except dans `OvhSmsBackend.send()`
- `export-facturation`: corriger POST pour utiliser les filtres, corriger filtres date
- `controle-bdc-form`: afficher les erreurs de validation du formulaire sidebar, corriger mutation GET
- `formulaire-creation-bdc`: transaction atomique dans `creer_bdc`
- `upload-pdf`: ajouter limite taille serveur
- `extraction-pdf-erilia`: guard `InvalidOperation` dans `_convertir_montant_fr`
- `modeles-donnees-bdc`: contrainte unique `(sous_traitant, numero)` sur `ReleveFacturation`
- `projet-django-config`: supprimer credentials du login.html, auth sur media LAN

## Impact

- **Services** : `apps/bdc/services.py` (4 fonctions + transaction.atomic)
- **Vues** : `apps/bdc/views.py` (RBAC, export, sidebar, forfait, mark_safe, upload, checklist GET)
- **Vues bibliotheque** : `apps/bdc/views_bibliotheque.py` (validation modifier)
- **Comptes** : `apps/accounts/views.py` (RBAC gestion)
- **Notifications** : `apps/notifications/email.py`, `apps/notifications/backends.py`
- **Parsers** : `apps/pdf_extraction/erilia_parser.py`
- **Modeles** : `apps/bdc/models.py` (contrainte unique releve)
- **Filtres** : `apps/bdc/filters.py` (date lookup)
- **Exports** : `apps/bdc/releves_export.py` (Content-Disposition)
- **Templates** : `templates/accounts/login.html`
- **Config** : `config/urls.py` (media auth LAN)
- **Migration** : 1 nouvelle migration pour la contrainte unique
