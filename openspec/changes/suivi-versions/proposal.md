## Why

L'application est en production depuis plusieurs mois et évolue en continu, mais rien ne permet aujourd'hui de savoir, depuis l'interface, quelle version tourne, quand elle a été mise en ligne, ni ce qui a changé depuis la dernière fois. Les utilisateurs (Secrétaires, CDT) découvrent les évolutions sans contexte, et il n'existe aucun historique consultable des mises à jour livrées.

## What Changes

- Nouveau modèle `Version` (numéro CalVer par date, ex. `2026.08.15`, résumé et liste de changements) créé manuellement (admin Django) au moment de déployer un lot de changes archivés.
- Nouvelle page `/nouveautes/` listant les versions par date décroissante, accessible à tous les utilisateurs authentifiés.
- Nouveau badge de version dans la sidebar (`templates/base.html`), visible par tous, pointant vers `/nouveautes/`.
- Aucune intégration avec git (pas de tag, pas de lecture de `.git` au runtime) : la base de données est l'unique source de vérité pour la V1.

## Capabilities

### New Capabilities
- `suivi-versions` : Permettre de publier et consulter, depuis l'interface ISMA, l'historique des versions de l'application (numéro, date de mise en ligne, résumé des changements), à destination de tous les utilisateurs.

### Modified Capabilities
- `base-template-ui` : Ajout d'un badge de version dans la sidebar, visible par tous les utilisateurs, pointant vers la page `/nouveautes/`.

## Impact

- Nouvelle app Django `apps/changelog/` (modèle, vues, urls, templates, admin).
- `config/urls.py` : ajout de l'inclusion des urls de la nouvelle app.
- `config/settings/base.py` : ajout de l'app à `LOCAL_APPS`.
- `templates/base.html` : ajout du badge de version dans la sidebar.
- Aucun impact sur `scripts/deploy.sh` ni sur le Dockerfile pour cette V1.
