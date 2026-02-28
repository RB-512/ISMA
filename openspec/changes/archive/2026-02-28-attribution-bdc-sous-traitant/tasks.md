## 1. Formulaire et routes

- [x] 1.1 Créer `AttributionForm` dans `forms.py` : champs `sous_traitant` (queryset ST actifs), `pourcentage_st`
- [x] 1.2 Ajouter les routes `<int:pk>/attribuer/` et `<int:pk>/reattribuer/` dans `urls.py`

## 2. Logique métier (services.py)

- [x] 2.1 Créer `attribuer_st(bdc, sous_traitant, pourcentage, utilisateur)` : valide statut A_FAIRE, assigne ST + pourcentage, calcule montant_st, passe en EN_COURS, trace ATTRIBUTION
- [x] 2.2 Créer `reattribuer_st(bdc, nouveau_st, pourcentage, utilisateur)` : valide statut EN_COURS, sauvegarde ancien ST, assigne nouveau, recalcule montant, trace REATTRIBUTION

## 3. Notifications (stub)

- [x] 3.1 Créer `notifications.py` avec `notifier_st_attribution(bdc)` : construit le message SMS (adresse, occupation, accès, travaux, SANS prix), logge via logger.info

## 4. Vues

- [x] 4.1 Créer `attribuer_bdc` (GET + POST, `@group_required("CDT")`) : valide statut A_FAIRE, affiche formulaire, appelle `attribuer_st()` + `notifier_st_attribution()`, redirige
- [x] 4.2 Créer `reattribuer_bdc` (GET + POST, `@group_required("CDT")`) : valide statut EN_COURS, affiche formulaire pré-rempli, appelle `reattribuer_st()` + `notifier_st_attribution()`, redirige

## 5. Templates

- [x] 5.1 Créer `templates/bdc/attribuer.html` : formulaire d'attribution avec résumé BDC
- [x] 5.2 Modifier `templates/bdc/detail.html` : bouton "Attribuer" pour CDT (A_FAIRE), bouton "Réattribuer" pour CDT (EN_COURS), masquer transition A_FAIRE→EN_COURS des boutons statut
- [x] 5.3 Créer `templates/sous_traitants/list.html` : liste des ST actifs

## 6. Enrichir detail_bdc view

- [x] 6.1 Enrichir `detail_bdc` : passer `is_cdt` (bool) au template, filtrer transitions pour masquer EN_COURS si A_FAIRE

## 7. Tests

- [x] 7.1 Tests unitaires `attribuer_st()` et `reattribuer_st()` dans services
- [x] 7.2 Tests unitaires `notifier_st_attribution()` (message sans prix, logging)
- [x] 7.3 Tests vues `attribuer_bdc` et `reattribuer_bdc` (accès CDT, statut incorrect, POST valide)
- [x] 7.4 Tests template detail : bouton Attribuer/Réattribuer conditionnel

## 8. Validation

- [x] 8.1 Lancer `pytest` et `ruff check` — tous les tests passent, pas de lint
