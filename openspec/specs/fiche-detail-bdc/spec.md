## ADDED Requirements

### Requirement: La fiche détail affiche les contacts occupant et émetteur
La fiche détail BDC SHALL afficher une section **Contacts** avec le nom, téléphone et email de l'occupant, ainsi que le nom et téléphone de l'émetteur bailleur. Les champs vides SHALL être masqués. Si aucun contact n'est renseigné, la section SHALL être masquée.

#### Scenario: Affichage des contacts occupant complets
- **WHEN** le BDC a `occupant_nom`, `occupant_telephone` et `occupant_email` renseignés
- **THEN** la section Contacts affiche les trois champs occupant avec leurs valeurs

#### Scenario: Affichage de l'émetteur bailleur
- **WHEN** le BDC a `emetteur_nom` et `emetteur_telephone` renseignés
- **THEN** la section Contacts affiche le nom et téléphone de l'émetteur

#### Scenario: Contact partiellement renseigné
- **WHEN** seul `occupant_nom` est renseigné (pas de tél ni email)
- **THEN** seul le nom de l'occupant est affiché, les champs vides sont masqués

#### Scenario: Aucun contact renseigné
- **WHEN** tous les champs contacts sont vides
- **THEN** la section Contacts n'est pas affichée

### Requirement: La fiche détail affiche le sous-traitant attribué
La fiche détail SHALL afficher le sous-traitant attribué au BDC quand il existe. Le montant ST et le pourcentage ST ne SHALL pas être affichés (confidentiels).

#### Scenario: BDC avec sous-traitant attribué
- **WHEN** le BDC a un `sous_traitant` renseigné
- **THEN** le nom du sous-traitant est affiché dans la section Travaux

#### Scenario: BDC sans sous-traitant
- **WHEN** le BDC n'a pas de `sous_traitant`
- **THEN** aucune information sous-traitant n'est affichée

### Requirement: La secrétaire peut éditer les champs manuels depuis la fiche détail
La fiche détail SHALL afficher un formulaire d'édition pour les champs manuels : `occupation` (select vacant/occupé), `modalite_acces` (textarea), `rdv_pris` (checkbox), `rdv_date` (datetime), `notes` (textarea). Le formulaire SHALL être visible uniquement pour les utilisateurs du groupe "Secretaire". La soumission SHALL sauvegarder les champs et enregistrer une action MODIFICATION dans l'historique.

#### Scenario: Affichage du formulaire pour une secrétaire
- **WHEN** un utilisateur du groupe "Secretaire" accède à la fiche détail
- **THEN** le formulaire d'édition des champs manuels est affiché avec les valeurs actuelles pré-remplies

#### Scenario: Formulaire masqué pour un non-secrétaire
- **WHEN** un utilisateur authentifié hors groupe "Secretaire" accède à la fiche détail
- **THEN** les champs manuels sont affichés en lecture seule, sans formulaire d'édition

#### Scenario: Soumission du formulaire avec succès
- **WHEN** une secrétaire soumet le formulaire avec `occupation=OCCUPE` et `notes="Clé chez gardien"`
- **THEN** le BDC est mis à jour, une action MODIFICATION est tracée dans l'historique, et la page est rechargée avec un message de succès

#### Scenario: Soumission avec formulaire invalide
- **WHEN** une secrétaire soumet le formulaire avec des données invalides
- **THEN** le formulaire est ré-affiché avec les erreurs de validation

### Requirement: La vue modifier_bdc accepte les modifications POST
`modifier_bdc` SHALL être une vue POST-only accessible uniquement au groupe "Secretaire". Elle SHALL accepter les champs `occupation`, `modalite_acces`, `rdv_pris`, `rdv_date`, `notes`. Elle SHALL enregistrer une action MODIFICATION dans l'historique et rediriger vers la fiche détail.

#### Scenario: POST valide par une secrétaire
- **WHEN** une secrétaire POST sur `/<pk>/modifier/` avec des champs valides
- **THEN** le BDC est modifié, l'historique est tracé, et l'utilisateur est redirigé vers la fiche détail avec un message de succès

#### Scenario: Accès GET refusé
- **WHEN** un GET est envoyé sur `/<pk>/modifier/`
- **THEN** la requête est refusée (405 Method Not Allowed ou redirection)

#### Scenario: Accès non-secrétaire refusé
- **WHEN** un utilisateur hors groupe "Secretaire" POST sur `/<pk>/modifier/`
- **THEN** l'accès est refusé (403 ou redirection login)

### Requirement: La secrétaire peut changer le statut depuis la fiche détail
La fiche détail SHALL afficher des boutons pour chaque transition de statut autorisée depuis le statut courant. Chaque bouton SHALL soumettre un POST vers `changer_statut_bdc`. La logique de transition existante (`changer_statut` dans services.py) SHALL être réutilisée. La transition `A_FAIRE → EN_COURS` SHALL être masquée des boutons de statut car elle est gérée par l'attribution. Un bouton "Attribuer" séparé SHALL être affiché pour les utilisateurs CDT quand le BDC est en statut `A_FAIRE`. Un bouton "Réattribuer" SHALL être affiché pour les CDT quand le statut est `EN_COURS`.

#### Scenario: Affichage des boutons de transition
- **WHEN** le BDC est au statut `A_TRAITER` et les transitions autorisées sont `[A_FAIRE]`
- **THEN** un bouton "Enregistrer → À faire" est affiché

#### Scenario: Statut terminal sans boutons
- **WHEN** le BDC est au statut `FACTURE` (terminal)
- **THEN** aucun bouton de transition n'est affiché

#### Scenario: Transition réussie
- **WHEN** une secrétaire clique sur le bouton de transition vers `A_FAIRE` et l'occupation est renseignée
- **THEN** le statut est changé via `changer_statut()`, l'historique est tracé, et la page est rechargée avec le nouveau statut

#### Scenario: Transition refusée — occupation manquante
- **WHEN** une secrétaire clique sur le bouton "À faire" mais `occupation` est vide
- **THEN** un message d'erreur est affiché : "Le champ Vacant / Occupé est obligatoire"

#### Scenario: Boutons masqués pour non-secrétaire
- **WHEN** un utilisateur hors groupe "Secretaire" voit la fiche
- **THEN** les boutons de transition ne sont pas affichés

#### Scenario: Bouton Attribuer pour CDT sur BDC A_FAIRE
- **WHEN** un utilisateur CDT voit un BDC en statut `A_FAIRE`
- **THEN** un bouton "Attribuer" est affiché, pointant vers `/<pk>/attribuer/`

#### Scenario: Bouton Réattribuer pour CDT sur BDC EN_COURS
- **WHEN** un utilisateur CDT voit un BDC en statut `EN_COURS` avec un ST attribué
- **THEN** un bouton "Réattribuer" est affiché, pointant vers `/<pk>/reattribuer/`

#### Scenario: Transition A_FAIRE vers EN_COURS masquée
- **WHEN** le BDC est en statut `A_FAIRE` et la secrétaire voit les boutons de transition
- **THEN** la transition vers `EN_COURS` n'est pas dans les boutons (gérée par l'attribution)

### Requirement: La vue changer_statut_bdc applique la transition
`changer_statut_bdc` SHALL être une vue POST-only accessible uniquement au groupe "Secretaire". Elle SHALL recevoir le `nouveau_statut` en POST, appeler `changer_statut()` du service, et rediriger vers la fiche détail.

#### Scenario: Transition valide
- **WHEN** une secrétaire POST sur `/<pk>/statut/` avec `nouveau_statut=A_FAIRE`
- **THEN** `changer_statut()` est appelé, le BDC est mis à jour, et l'utilisateur est redirigé avec un message de succès

#### Scenario: Transition invalide
- **WHEN** le POST contient un `nouveau_statut` non autorisé depuis le statut courant
- **THEN** un message d'erreur est affiché et le statut reste inchangé

#### Scenario: BDC incomplet
- **WHEN** la transition échoue à cause d'un `BDCIncomplet` (ex: occupation manquante)
- **THEN** un message d'erreur est affiché avec le détail de l'erreur

### Requirement: L'historique affiche les détails des changements de statut
La section historique SHALL afficher, pour les actions `STATUT_CHANGE`, l'ancien et le nouveau statut extraits du champ `details` JSON.

#### Scenario: Historique avec changement de statut
- **WHEN** l'historique contient une action `STATUT_CHANGE` avec `details={"ancien_statut": "A_TRAITER", "nouveau_statut": "A_FAIRE"}`
- **THEN** la ligne affiche "Changement de statut : À traiter → À faire"

#### Scenario: Historique sans détails
- **WHEN** l'historique contient une action sans `details`
- **THEN** seul le libellé de l'action est affiché (comportement actuel préservé)

### Requirement: Les routes URL sont configurées pour les nouvelles vues
Le fichier `urls.py` SHALL contenir les routes `<int:pk>/modifier/` et `<int:pk>/statut/` pointant vers les vues `modifier_bdc` et `changer_statut_bdc`.

#### Scenario: Route modifier
- **WHEN** un POST est envoyé sur `/bdc/42/modifier/`
- **THEN** la vue `modifier_bdc` est appelée avec `pk=42`

#### Scenario: Route statut
- **WHEN** un POST est envoyé sur `/bdc/42/statut/`
- **THEN** la vue `changer_statut_bdc` est appelée avec `pk=42`
