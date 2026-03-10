## Requirements

### Requirement: Modèle SousTraitant enrichi avec SIRET et adresse

Le systeme SHALL etendre le modele SousTraitant avec les champs : `siret` (CharField, 14 caracteres, blank=True, unique si renseigne), `adresse` (CharField, blank=True), `code_postal` (CharField, 5 caracteres, blank=True), `ville` (CharField, blank=True). Les champs existants (nom, telephone, email, actif) restent inchanges.

#### Scenario: SIRET valide accepte
- **WHEN** un utilisateur saisit un SIRET de 14 chiffres
- **THEN** le formulaire est valide et le sous-traitant est enregistre

#### Scenario: SIRET invalide rejete
- **WHEN** un utilisateur saisit un SIRET qui n'a pas exactement 14 chiffres
- **THEN** le formulaire est invalide avec une erreur sur le champ siret

#### Scenario: SIRET en doublon rejete
- **WHEN** un utilisateur saisit un SIRET deja utilise par un autre sous-traitant
- **THEN** le formulaire est invalide avec une erreur d'unicite

#### Scenario: SIRET vide accepte
- **WHEN** un utilisateur laisse le champ SIRET vide
- **THEN** le formulaire est valide (SIRET optionnel)

### Requirement: Creation d'un sous-traitant par le CDT

Le systeme SHALL permettre au CDT de creer un sous-traitant via un formulaire integre a la page liste. Les champs obligatoires sont : nom, telephone. Les champs optionnels sont : email, siret, adresse, code_postal, ville.

#### Scenario: Creation reussie
- **WHEN** le CDT remplit le formulaire avec nom et telephone et soumet
- **THEN** le sous-traitant est cree, un message de succes est affiche, et la liste est mise a jour

#### Scenario: Nom en doublon rejete
- **WHEN** le CDT saisit un nom deja existant
- **THEN** le formulaire est invalide avec une erreur d'unicite sur le champ nom

#### Scenario: Secretaire ne peut pas creer
- **WHEN** un utilisateur du groupe Secretaire tente d'acceder a la creation
- **THEN** l'acces est refuse (403 Forbidden)

### Requirement: Modification d'un sous-traitant par le CDT

Le systeme SHALL permettre au CDT de modifier les informations d'un sous-traitant via un formulaire HTMX charge dans un modal.

#### Scenario: Modification reussie
- **WHEN** le CDT modifie le telephone et soumet le formulaire
- **THEN** le sous-traitant est mis a jour et un message de succes est affiche

#### Scenario: Modification avec SIRET en doublon
- **WHEN** le CDT modifie le SIRET vers une valeur deja utilisee par un autre ST
- **THEN** le formulaire est invalide avec une erreur d'unicite

### Requirement: Desactivation et reactivation d'un sous-traitant

Le systeme SHALL permettre au CDT de desactiver un sous-traitant actif (actif=False) et de reactiver un sous-traitant inactif (actif=True). La suppression physique n'est pas autorisee.

#### Scenario: Desactivation reussie
- **WHEN** le CDT clique sur "Desactiver" pour un sous-traitant actif
- **THEN** le sous-traitant passe a actif=False et un message de succes est affiche

#### Scenario: Reactivation reussie
- **WHEN** le CDT clique sur "Reactiver" pour un sous-traitant inactif
- **THEN** le sous-traitant passe a actif=True et un message de succes est affiche

#### Scenario: ST desactive n'apparait plus dans les attributions
- **WHEN** un sous-traitant est desactive
- **THEN** il n'apparait plus dans le dropdown d'attribution des BDC

### Requirement: Vue liste avec recherche et affichage complet

Le systeme SHALL afficher la liste de tous les sous-traitants (actifs et inactifs) avec les colonnes : nom, SIRET, telephone, email, ville, statut. La liste SHALL supporter la recherche par nom, SIRET, ou ville via un champ de recherche GET.

#### Scenario: Liste affiche tous les sous-traitants
- **WHEN** le CDT ou la Secretaire accede a la page sous-traitants
- **THEN** tous les sous-traitants sont affiches avec leur statut (actif/inactif)

#### Scenario: Recherche par nom
- **WHEN** l'utilisateur saisit "Dupont" dans le champ de recherche
- **THEN** seuls les sous-traitants dont le nom, SIRET, ou ville contient "Dupont" sont affiches

#### Scenario: Sous-traitants inactifs affiches en opacite reduite
- **WHEN** un sous-traitant est inactif
- **THEN** sa ligne est affichee en opacite reduite avec un badge "Inactif"
