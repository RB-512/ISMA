## 1. Formulaire et routes

- [x] 1.1 Créer `BDCEditionForm` dans `forms.py` avec les champs `occupation`, `modalite_acces`, `rdv_pris`, `rdv_date`, `notes`
- [x] 1.2 Ajouter les routes `<int:pk>/modifier/` et `<int:pk>/statut/` dans `urls.py`

## 2. Vues backend

- [x] 2.1 Créer la vue `modifier_bdc` (POST-only, `@group_required("Secretaire")`) : valide `BDCEditionForm`, sauvegarde, trace MODIFICATION, redirige
- [x] 2.2 Créer la vue `changer_statut_bdc` (POST-only, `@group_required("Secretaire")`) : appelle `changer_statut()`, gère `TransitionInvalide` et `BDCIncomplet`, redirige
- [x] 2.3 Enrichir `detail_bdc` : passer `form_edition` (instance `BDCEditionForm`), `transitions` (liste des statuts cibles autorisés), `is_secretaire` (bool) au template

## 3. Template detail.html

- [x] 3.1 Ajouter la section Contacts (occupant + émetteur), masquée si aucun contact
- [x] 3.2 Ajouter le sous-traitant dans la section Travaux (conditionnel)
- [x] 3.3 Ajouter le formulaire d'édition des champs manuels (conditionnel `is_secretaire`)
- [x] 3.4 Ajouter les boutons de transition de statut (conditionnel `is_secretaire` + transitions non vides)
- [x] 3.5 Enrichir l'historique avec les détails de changement de statut (ancien → nouveau)

## 4. Tests

- [x] 4.1 Tests unitaires : `test_modifier_bdc` (POST valide, accès refusé non-secrétaire, GET refusé)
- [x] 4.2 Tests unitaires : `test_changer_statut_bdc` (transition valide, transition invalide, BDCIncomplet, accès refusé)
- [x] 4.3 Tests unitaires : `test_detail_bdc` (contacts affichés, formulaire conditionnel, transitions affichées)

## 5. Validation

- [x] 5.1 Lancer `pytest` et `ruff check` — tous les tests passent, pas de lint
