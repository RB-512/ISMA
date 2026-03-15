## MODIFIED Requirements

### Requirement: Variables de substitution email attribution
Le systeme DOIT fournir la variable `{nom_st}` (nom du sous-traitant) dans les variables de substitution disponibles pour le template email d'attribution.

#### Scenario: Objet par defaut avec nom ST
- **WHEN** un email d'attribution est envoye avec le template par defaut
- **THEN** l'objet contient le numero BDC et le nom du sous-traitant (format : `BDC {numero_bdc} — Attribution — {nom_st}`)

#### Scenario: Template personnalise avec nom ST
- **WHEN** l'admin a configure un sujet personnalise contenant `{nom_st}`
- **THEN** le nom du sous-traitant est substitue dans l'objet
