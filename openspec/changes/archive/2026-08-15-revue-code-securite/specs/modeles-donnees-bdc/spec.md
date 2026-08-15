## ADDED Requirements

### Requirement: Unicite numero releve par sous-traitant
Le modele `ReleveFacturation` DOIT avoir une contrainte `unique_together` sur `(sous_traitant, numero)` pour empecher les doublons de numero de releve par sous-traitant.

#### Scenario: Creation simultanee de deux releves
- **WHEN** deux utilisateurs creent un releve pour le meme sous-traitant en meme temps
- **THEN** le second recoit une erreur d'integrite au lieu de creer un doublon

### Requirement: Filename Content-Disposition quote
Les exports de releve DOIVENT entourer le filename dans le header `Content-Disposition` de guillemets pour gerer les caracteres speciaux.

#### Scenario: Nom sous-traitant avec accents
- **WHEN** un releve est exporte pour un sous-traitant nomme "Dupont & Fils"
- **THEN** le navigateur telecharge le fichier avec le nom correct
