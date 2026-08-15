## ADDED Requirements

### Requirement: Etage et porte dans le corps du mail d'attribution
Le corps du mail d'attribution SHALL inclure l'etage et la porte du logement lorsque ces informations sont renseignees sur le BDC.

#### Scenario: BDC avec etage et porte renseignes
- **WHEN** un mail d'attribution est envoye pour un BDC ayant `logement_etage` et `logement_porte` renseignes
- **THEN** le corps du mail contient une ligne "Etage / Porte : {etage} / {porte}"

#### Scenario: BDC sans etage ni porte
- **WHEN** un mail d'attribution est envoye pour un BDC sans `logement_etage` ni `logement_porte`
- **THEN** le corps du mail ne contient pas de ligne etage/porte (pas de ligne vide)

#### Scenario: Variables ConfigEmail
- **WHEN** un template personnalise est configure dans ConfigEmail
- **THEN** les variables `{etage}` et `{porte}` sont disponibles dans le template
