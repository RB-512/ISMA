## 1. Securite critique

- [x] 1.1 Supprimer le bloc credentials (email/mdp) dans `templates/accounts/login.html`
- [x] 1.2 Externaliser les credentials de `bdc-peinture/e2e/helpers.py` en variables d'environnement (SKIP: fichier non tracke dans git)
- [x] 1.3 Ajouter `@group_required('CDT')` sur les vues workflow dans `apps/bdc/views.py` : `attribuer_bdc`, `reattribuer_bdc`, `attribution_split`, `attribution_partial`, `valider_realisation_bdc`, `valider_facturation_bdc`, `renvoyer_controle_bdc`, `releve_creer`, `releve_valider`, `releve_retirer_bdc`
- [x] 1.4 Ajouter `@group_required('CDT')` sur toutes les vues de `apps/accounts/views.py` liees a `urls_gestion.py`
- [x] 1.5 Remplacer `mark_safe()` par `format_html()` dans `_msg_attribution` (`apps/bdc/views.py`)
- [x] 1.6 Adapter les tests existants impactes par les nouvelles permissions RBAC
- [x] 1.7 Ajouter des tests RBAC : Secretaire recoit 403 sur les vues CDT

## 2. Integrite des donnees

- [x] 2.1 Envelopper `attribuer_st` dans `transaction.atomic()` (`apps/bdc/services.py`)
- [x] 2.2 Envelopper `reattribuer_st` dans `transaction.atomic()` (`apps/bdc/services.py`)
- [x] 2.3 Envelopper `valider_realisation` dans `transaction.atomic()` (`apps/bdc/services.py`)
- [x] 2.4 Envelopper `valider_facturation` dans `transaction.atomic()` (`apps/bdc/services.py`)
- [x] 2.5 Envelopper `renvoyer_controle` dans `transaction.atomic()` (`apps/bdc/services.py`)
- [x] 2.6 Envelopper `changer_statut` dans `transaction.atomic()` (`apps/bdc/services.py`)
- [x] 2.7 Envelopper le bloc creation BDC + lignes + PDF dans `transaction.atomic()` (`apps/bdc/views.py`, vue `creer_bdc`)
- [x] 2.8 Ajouter contrainte `unique_together = [("sous_traitant", "numero")]` sur `ReleveFacturation` + migration (0016)
- [x] 2.9 Verifier l'absence de doublons existants avant migration (a faire en prod avant `migrate`)

## 3. Notifications resilientes

- [x] 3.1 Ajouter try/except dans `OvhSmsBackend.send()` — retourner `False` en cas d'erreur (`apps/notifications/backends.py`)
- [x] 3.2 Ajouter try/except ou `fail_silently=True` dans `envoyer_email_attribution()` (`apps/notifications/email.py`)
- [x] 3.3 Remplacer `format_map(variables)` par `format_map(defaultdict(str, variables))` dans `_preparer_email` (`apps/notifications/email.py`)

## 4. Corrections vues et formulaires

- [x] 4.1 Corriger `export_facturation` : utiliser `request.POST` quand `method == "POST"` (`apps/bdc/views.py`)
- [x] 4.2 Propager les erreurs de `BDCEditionForm` dans `sidebar_save_and_transition` (`apps/bdc/views.py`)
- [x] 4.3 Ajouter try/except `InvalidOperation` dans `_parse_lignes_forfait` (`apps/bdc/views.py`)
- [x] 4.4 Ajouter guard de statut dans `modifier_bdc` : refuser si statut >= EN_COURS (`apps/bdc/views.py`)
- [x] 4.5 Corriger `sidebar_checklist` GET : afficher formulaire de confirmation au lieu d'executer la transition (`apps/bdc/views.py`)
- [x] 4.6 Corriger `bibliotheque_modifier` : valider les champs avant `save()` (`apps/bdc/views_bibliotheque.py`)

## 5. Filtres et exports

- [x] 5.1 Changer `lookup_expr` de `date_du` a `"date__gte"` et `date_au` a `"date__lte"` (`apps/bdc/filters.py`)
- [x] 5.2 Ajouter guillemets autour du filename dans `Content-Disposition` (`apps/bdc/releves_export.py`)

## 6. Config et infrastructure

- [x] 6.1 Ajouter limite taille upload 10 Mo dans `upload_pdf` (`apps/bdc/views.py`)
- [x] 6.2 Ajouter wrapper authentifie pour servir les media en mode LAN (`config/urls.py`)
- [x] 6.3 Supprimer le decorateur `@login_required` orphelin (`apps/accounts/views.py` L261)

## 7. Parser PDF

- [x] 7.1 Ajouter try/except `InvalidOperation` dans `_convertir_montant_fr` (`apps/pdf_extraction/erilia_parser.py`)

## 8. Verification finale

- [x] 8.1 Lancer `uv run pytest -v --tb=short` — 495 passed, 0 failed
- [x] 8.2 Lancer `uv run ruff check .` — imports fixes, E402 pre-existantes ignorees
- [x] 8.3 Lancer `uv run manage.py makemigrations` — migration 0016 creee
