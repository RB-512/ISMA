## Purpose

Tenir l'étape entre le PDF déposé et le BDC enregistré : un formulaire pré-rempli avec ce
que l'extraction a trouvé, entièrement éditable, où la secrétaire corrige et complète avant
de valider. L'extraction n'est jamais tenue pour parfaite — le formulaire est l'endroit où
elle est relue.

Le périmètre s'arrête à cette étape de création. Ce qui arrive avant relève d'`upload-pdf`
et des parsers ; l'enrichissement ultérieur du dossier (occupation, accès, rendez-vous) et
sa mise en circulation relèvent de `controle-bdc-form`. Le formulaire reste accessible sans
upload préalable, pour les BDC saisis à la main.

## Requirements

### Requirement: Le formulaire de création est pré-rempli depuis l'extraction PDF
Le système SHALL afficher un formulaire `BonDeCommandeForm` dont les champs extraits (numéro, adresse, travaux, montants, etc.) sont pré-remplis et éditables. Les champs non extraits restent vides pour saisie manuelle. Tous les widgets de formulaire SHALL utiliser le style du design system Isma (bordures arrondies, focus ring accent, typographie cohérente, support dark mode).

#### Scenario: Accès au formulaire après upload réussi
- **WHEN** la secrétaire est redirigée après un upload réussi
- **THEN** le formulaire affiche les données extraites dans les champs stylisés avec le design system Isma

#### Scenario: Accès direct sans upload préalable
- **WHEN** la secrétaire accède à `/bdc/nouveau/` sans avoir préalablement uploadé un PDF (session vide)
- **THEN** le système affiche le formulaire vide (création manuelle) avec tous les champs stylisés
