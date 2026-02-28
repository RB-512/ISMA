## MODIFIED Requirements

### Requirement: La fiche détail affiche le sous-traitant attribué
La fiche détail SHALL afficher le sous-traitant attribué au BDC quand il existe. Le montant ST et le pourcentage ST ne SHALL pas être affichés (confidentiels). Un bouton "BDC terrain" SHALL être affiché quand le champ `pdf_terrain` est renseigné, permettant le téléchargement du PDF sans prix.

#### Scenario: BDC avec sous-traitant attribué
- **WHEN** le BDC a un `sous_traitant` renseigné
- **THEN** le nom du sous-traitant est affiché dans la section Travaux

#### Scenario: BDC sans sous-traitant
- **WHEN** le BDC n'a pas de `sous_traitant`
- **THEN** aucune information sous-traitant n'est affichée

#### Scenario: Bouton BDC terrain visible
- **WHEN** le BDC a un `pdf_terrain` renseigné
- **THEN** un bouton "BDC terrain" est affiché dans l'en-tête, pointant vers `/<pk>/terrain/`

#### Scenario: Bouton BDC terrain masqué
- **WHEN** le BDC n'a pas de `pdf_terrain`
- **THEN** le bouton "BDC terrain" n'est pas affiché
