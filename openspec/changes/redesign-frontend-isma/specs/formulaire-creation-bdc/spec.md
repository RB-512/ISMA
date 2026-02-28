## MODIFIED Requirements

### Requirement: Le formulaire de création est pré-rempli depuis l'extraction PDF
Le système SHALL afficher un formulaire `BonDeCommandeForm` dont les champs extraits (numéro, adresse, travaux, montants, etc.) sont pré-remplis et éditables. Les champs non extraits restent vides pour saisie manuelle. Tous les widgets de formulaire SHALL utiliser le style du design system Isma (bordures arrondies, focus ring accent, typographie cohérente, support dark mode).

#### Scenario: Accès au formulaire après upload réussi
- **WHEN** la secrétaire est redirigée après un upload réussi
- **THEN** le formulaire affiche les données extraites dans les champs stylisés avec le design system Isma

#### Scenario: Accès direct sans upload préalable
- **WHEN** la secrétaire accède à `/bdc/nouveau/` sans avoir préalablement uploadé un PDF (session vide)
- **THEN** le système affiche le formulaire vide (création manuelle) avec tous les champs stylisés
