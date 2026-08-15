## Context

Le projet BDC Peinture est en production sur un VPS OVH (51.83.197.18). Une revue de code globale a identifie 22 issues reparties en 3 categories : securite (credentials exposes, RBAC manquant, XSS), integrite des donnees (transactions manquantes, race conditions), et robustesse (exceptions non gerees, validations manquantes).

Le code est fonctionnel mais a ete developpe rapidement (MVP). Les tests unitaires couvrent bien le workflow metier mais ne testent pas les permissions RBAC au-dela de `@login_required`.

## Goals / Non-Goals

**Goals:**
- Corriger les 22 issues identifiees sans casser les fonctionnalites existantes
- Chaque correction doit etre minimale et ciblee (pas de refactoring)
- Les tests existants doivent continuer a passer (`uv run pytest`)
- Ajouter des tests pour les corrections RBAC

**Non-Goals:**
- Refactoring general du code (pas de reorganisation des vues, pas de CBV)
- Ajout de nouvelles fonctionnalites
- Migration vers un systeme de permissions plus complexe (django-guardian, etc.)
- Audit de performance ou optimisation des requetes

## Decisions

### 1. RBAC : `@group_required` decorateur par vue (pas de middleware)

Le projet utilise deja `@group_required` dans `apps/accounts/decorators.py`. On l'ajoute sur les vues qui en ont besoin plutot que de creer un middleware global.

**Pourquoi :** un middleware necessiterait une table de mapping URL→groupe, plus complexe et risque de regression. Le decorateur est deja le pattern etabli.

**Mapping des vues :**
- CDT uniquement : `attribuer_bdc`, `reattribuer_bdc`, `attribution_split`, `attribution_partial`, `valider_realisation_bdc`, `valider_facturation_bdc`, `renvoyer_controle_bdc`, `releve_creer`, `releve_valider`, `releve_retirer_bdc`, toutes les vues de `urls_gestion.py`
- Secretaire + CDT (login_required suffit) : `upload_pdf`, `creer_bdc`, `modifier_bdc`, `liste_bdc`, `detail_bdc`, `export_facturation`

### 2. Transactions : `transaction.atomic()` au niveau service

On enveloppe les fonctions service, pas les vues. Le pattern est : la vue appelle le service dans un contexte atomique implicite (le service gere sa propre transaction).

**Fonctions a envelopper :**
- `attribuer_st()`, `reattribuer_st()`, `valider_realisation()`, `valider_facturation()`, `renvoyer_controle()`, `changer_statut()`
- Dans `views.py` : le bloc `creer_bdc` (bdc.save + lignes + pdf)

### 3. Notifications : try/except au niveau backend, pas au niveau appelant

`OvhSmsBackend.send()` doit gerer ses propres erreurs et retourner `False`. `envoyer_email_attribution()` doit utiliser `fail_silently=True` ou un try/except. Le contrat est : les notifications ne bloquent jamais le workflow.

### 4. Credentials : suppression du bloc dans login.html, pas de conditionnel

On supprime le bloc `Dev —` completement plutot que de le conditionner sur `{% if debug %}`, car `DEBUG` ne devrait pas etre accessible dans les templates en prod de toute facon, et le bloc n'a pas de valeur en dev non plus (les devs connaissent les credentials).

### 5. Migration : une seule migration pour la contrainte unique

`unique_together = [("sous_traitant", "numero")]` sur `ReleveFacturation`. Avant de migrer, verifier qu'il n'y a pas de doublons existants en prod.

### 6. Filtres date : `date__lte` / `date__gte` sur DateTimeField

Changer le `lookup_expr` de `"lte"` a `"date__lte"` et `"gte"` a `"date__gte"` pour que les bornes incluent les records crees durant toute la journee.

## Risks / Trade-offs

- **RBAC sur vues existantes** → Les tests existants qui testent l'acces Secretaire sur les vues CDT vont echouer. Il faudra les adapter (tester avec `client_cdt` au lieu de `client_secretaire`).
  Mitigation : identifier les tests impactes avant de modifier les vues.

- **`transaction.atomic()` et notifications** → Si les notifications sont dans le bloc atomique et levent une exception, le rollback annule tout.
  Mitigation : les notifications sont appelees APRES le `bdc.save()` final dans `attribuer_st`, donc elles seront en dehors du bloc atomique ou dans leur propre try/except.

- **Contrainte unique `ReleveFacturation`** → Si des doublons existent deja en prod, la migration echoue.
  Mitigation : script de verification avant migration (`SELECT sous_traitant_id, numero, COUNT(*) ... HAVING COUNT(*) > 1`).

- **`export_facturation` POST** → Le changement de `request.GET` a `request.POST` peut casser le formulaire si le template utilise `method="GET"`.
  Mitigation : verifier le template pour confirmer que le form utilise bien `method="POST"`.

## Open Questions

_(aucune — toutes les corrections sont bien definies et ciblees)_
