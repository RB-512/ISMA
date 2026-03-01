## ADDED Requirements

### Requirement: Formulaire de contrôle bloque la transition si invalide
Lors du POST sur la vue de contrôle, si le formulaire d'édition n'est pas valide (`form.is_valid()` retourne False), la transition de statut ne SHALL PAS être tentée. Le formulaire lié (avec ses erreurs) SHALL être conservé pour re-rendu.

#### Scenario: Transition bloquée si occupation manquante
- **WHEN** l'utilisateur soumet le formulaire de contrôle avec `nouveau_statut=A_FAIRE` mais sans renseigner le champ `occupation`
- **THEN** la transition n'est pas effectuée, le statut du BDC reste `A_TRAITER`, et le formulaire est re-rendu avec une erreur sur le champ `occupation`

#### Scenario: Transition bloquée si rdv_date manquante pour logement occupé
- **WHEN** l'utilisateur soumet le formulaire de contrôle avec `occupation=OCCUPE` et `nouveau_statut=A_FAIRE` mais sans renseigner `rdv_date`
- **THEN** la transition n'est pas effectuée, le statut du BDC reste `A_TRAITER`, et le formulaire est re-rendu avec une erreur sur le champ `rdv_date`

#### Scenario: Transition bloquée si type_acces manquant pour logement vacant
- **WHEN** l'utilisateur soumet le formulaire de contrôle avec `occupation=VACANT` et `nouveau_statut=A_FAIRE` mais sans renseigner `type_acces`
- **THEN** la transition n'est pas effectuée, le statut du BDC reste `A_TRAITER`, et le formulaire est re-rendu avec une erreur sur le champ `type_acces`

### Requirement: Erreurs de champ affichées dans le template contrôle
Le template `controle.html` SHALL afficher les erreurs de validation de champ (`form_edition.<field>.errors`) à côté de chaque champ du formulaire.

#### Scenario: Erreur visible sur le champ occupation
- **WHEN** le formulaire est soumis sans valeur pour `occupation`
- **THEN** le template affiche un message d'erreur visible à côté du champ `occupation` dans le panneau droit

#### Scenario: Erreur visible sur le champ rdv_date
- **WHEN** le formulaire est soumis avec `occupation=OCCUPE` sans `rdv_date`
- **THEN** le template affiche un message d'erreur visible à côté du champ `rdv_date`

### Requirement: Sauvegarde simple (sans transition) fonctionne indépendamment de la validité du formulaire de transition
Le bouton "Enregistrer" (sans `nouveau_statut`) SHALL sauvegarder les données du formulaire si `form.is_valid()` retourne True, indépendamment de toute logique de transition.

#### Scenario: Enregistrement simple réussi
- **WHEN** l'utilisateur soumet le formulaire avec le bouton "Enregistrer" (sans nouveau_statut) avec toutes les données valides
- **THEN** le BDC est sauvegardé, une action MODIFICATION est tracée, et l'utilisateur reste sur la page de contrôle
