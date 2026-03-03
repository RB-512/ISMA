## 1. Formulaires

- [ ] 1.1 Ajouter le champ `email` (EmailField, obligatoire) a `CreerUtilisateurForm` avec validation unicite et creation `EmailAddress` allauth dans `save()`
- [ ] 1.2 Creer `ModifierUtilisateurForm` (ModelForm) avec champs `first_name`, `last_name`, `email`, `role` — synchronisation EmailAddress allauth dans `save()`
- [ ] 1.3 Ecrire les tests unitaires des formulaires (creation avec email, unicite email, modification avec sync allauth)

## 2. Vues

- [ ] 2.1 Modifier `creer_utilisateur` pour gerer le nouveau formulaire avec email
- [ ] 2.2 Creer la vue `modifier_utilisateur(request, pk)` — GET affiche le formulaire pre-rempli (partial HTMX), POST sauvegarde les modifications
- [ ] 2.3 Creer la vue `reset_password_utilisateur(request, pk)` — genere un mot de passe aleatoire, retourne le mot de passe dans la reponse HTMX
- [ ] 2.4 Creer la vue `reactiver_utilisateur(request, pk)` — met `is_active=True`
- [ ] 2.5 Ajouter les protections : CDT ne peut pas modifier son propre role, ni reset son propre mot de passe
- [ ] 2.6 Ecrire les tests des vues (permissions CDT, creation, modification, reset, reactivation, auto-protection)

## 3. URLs

- [ ] 3.1 Ajouter les routes dans `urls_gestion.py` : `<int:pk>/modifier/`, `<int:pk>/reset-password/`, `<int:pk>/reactiver/`

## 4. Templates

- [ ] 4.1 Mettre a jour `utilisateurs.html` — afficher email et statut actif/inactif dans la liste, ajouter boutons modifier/reset/reactiver
- [ ] 4.2 Creer le partial `_modifier_utilisateur.html` — formulaire de modification charge en HTMX (modal ou inline)
- [ ] 4.3 Creer le partial `_reset_password_result.html` — affichage du mot de passe temporaire (toast ou modal)
- [ ] 4.4 Ajouter le bouton reactiver (visible si `is_active=False`) avec confirmation

## 5. Validation finale

- [ ] 5.1 Lancer les tests (`uv run pytest`) et le linting (`uv run ruff check .`)
- [ ] 5.2 Tester manuellement via Playwright : creation avec email, modification, reset password, desactivation, reactivation
