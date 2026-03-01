## 1. Corriger la vue controle_bdc (apps/bdc/views.py)

- [x] 1.1 Restructurer le bloc POST pour gater la transition sur `form.is_valid()` : remplacer `if nouveau_statut:` par `if nouveau_statut and form_valid:` (où `form_valid = form.is_valid()` est calculé une seule fois)
- [x] 1.2 Remplacer la ligne `form = BDCEditionForm(instance=bdc) if est_editable else None` (ligne 978, hors du bloc if/else) par un bloc `else:` qui initialise le formulaire seulement sur GET, en préservant le formulaire lié (avec ses erreurs) sur POST

## 2. Afficher les erreurs de champ dans le template (templates/bdc/controle.html)

- [x] 2.1 Ajouter `{{ form_edition.occupation.errors }}` sous le select `occupation`
- [x] 2.2 Ajouter `{{ form_edition.type_acces.errors }}` sous le select `type_acces` (dans le div `x-show="occupation === 'VACANT'"`)
- [x] 2.3 Ajouter `{{ form_edition.rdv_date.errors }}` sous le champ `rdv_date` (dans le div `x-show="occupation === 'OCCUPE'"`)

## 3. Ajouter les tests de régression (tests/test_bdc/test_controle.py)

- [x] 3.1 Ajouter un test `test_transition_bloquee_si_occupation_manquante` : POST avec `nouveau_statut=A_FAIRE` mais sans `occupation` → statut reste `A_TRAITER`, réponse 200
- [x] 3.2 Ajouter un test `test_transition_bloquee_si_rdv_date_manquante_occupe` : POST avec `occupation=OCCUPE`, `nouveau_statut=A_FAIRE`, sans `rdv_date` → statut reste `A_TRAITER`, réponse 200
- [x] 3.3 Ajouter un test `test_transition_bloquee_si_type_acces_manquant_vacant` : POST avec `occupation=VACANT`, `nouveau_statut=A_FAIRE`, sans `type_acces` → statut reste `A_TRAITER`, réponse 200
- [x] 3.4 Vérifier que tous les tests existants passent toujours : `uv run pytest tests/test_bdc/test_controle.py -v --tb=short`
