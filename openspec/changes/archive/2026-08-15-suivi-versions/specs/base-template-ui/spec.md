## ADDED Requirements

### Requirement: Badge de version dans l'en-tête de la sidebar
Le template `templates/base.html` SHALL afficher, sous le logo "ISMA" en en-tête de la sidebar, le numéro de la dernière version publiée de l'application (capacité `suivi-versions`), lorsqu'au moins une version existe.

#### Scenario: Badge visible sous le logo
- **WHEN** une page utilisant `base.html` est rendue et qu'au moins une `Version` existe en base
- **THEN** le numéro de la version la plus récente est affiché sous le logo, sous forme de lien vers `/nouveautes/`
