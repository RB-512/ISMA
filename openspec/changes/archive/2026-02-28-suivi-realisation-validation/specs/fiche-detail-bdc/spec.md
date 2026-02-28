## MODIFIED Requirements

### Requirement: La secrétaire peut changer le statut depuis la fiche détail
La fiche détail SHALL afficher des boutons pour chaque transition de statut autorisée depuis le statut courant. Chaque bouton SHALL soumettre un POST vers `changer_statut_bdc`. La logique de transition existante (`changer_statut` dans services.py) SHALL être réutilisée. La transition `A_FAIRE → EN_COURS` SHALL être masquée des boutons de statut car elle est gérée par l'attribution. Un bouton "Attribuer" séparé SHALL être affiché pour les utilisateurs CDT quand le BDC est en statut `A_FAIRE`. Un bouton "Réattribuer" SHALL être affiché pour les CDT quand le statut est `EN_COURS`. Un bouton "Valider réalisation" SHALL être affiché pour les CDT quand le statut est `EN_COURS`. Un bouton "Passer en facturation" SHALL être affiché pour les CDT quand le statut est `A_FACTURER`. Un bouton "Annuler validation" SHALL être affiché pour les CDT quand le statut est `A_FACTURER`.

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

#### Scenario: Bouton Valider réalisation pour CDT sur BDC EN_COURS
- **WHEN** un utilisateur CDT voit un BDC en statut `EN_COURS`
- **THEN** un bouton "Valider réalisation" est affiché, soumettant un POST vers `/<pk>/valider/`

#### Scenario: Bouton Passer en facturation pour CDT sur BDC A_FACTURER
- **WHEN** un utilisateur CDT voit un BDC en statut `A_FACTURER`
- **THEN** un bouton "Passer en facturation" est affiché, soumettant un POST vers `/<pk>/facturer/`

#### Scenario: Bouton Annuler validation pour CDT sur BDC A_FACTURER
- **WHEN** un utilisateur CDT voit un BDC en statut `A_FACTURER`
- **THEN** un bouton "Annuler validation" est affiché, permettant de revenir en EN_COURS
