## ADDED Requirements

### Requirement: Generation d'une fiche chantier PDF
Le systeme SHALL generer une fiche chantier PDF a partir des donnees en base, sans aucun prix ni montant, destinee au sous-traitant.

#### Scenario: Fiche complete
- **WHEN** la generation est demandee pour un BDC avec toutes les donnees renseignees
- **THEN** le PDF contient : numero BDC, code bailleur, residence, adresse complete, occupation, nom et telephone de l'occupant, liste des prestations (designation + quantite, SANS prix), commentaire CDT, date de RDV, delai

#### Scenario: Donnees partielles
- **WHEN** certains champs sont vides (pas d'occupant, pas de commentaire CDT, pas de RDV)
- **THEN** les sections correspondantes sont omises du PDF
- **AND** le PDF est quand meme genere avec les donnees disponibles

#### Scenario: Aucun prix visible
- **WHEN** la fiche est generee
- **THEN** aucun montant HT, prix unitaire, ou montant total n'apparait dans le PDF

### Requirement: Prestations listees sans prix
Le systeme SHALL afficher la liste des prestations du BDC avec leur designation et quantite, mais SANS prix unitaire ni montant.

#### Scenario: BDC avec plusieurs lignes de prestation
- **WHEN** un BDC a 3 lignes de prestation
- **THEN** la fiche liste les 3 designations avec leurs quantites
- **AND** aucune colonne prix/montant n'est presente

### Requirement: Commentaire CDT
Le systeme SHALL inclure le commentaire saisi par le CDT lors de l'attribution dans la fiche chantier.

#### Scenario: Commentaire renseigne
- **WHEN** le CDT a saisi un commentaire lors de l'attribution
- **THEN** le commentaire apparait dans une section "Consignes" de la fiche

#### Scenario: Pas de commentaire
- **WHEN** le champ commentaire est vide
- **THEN** la section "Consignes" n'apparait pas dans la fiche
