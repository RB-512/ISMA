## ADDED Requirements

### Requirement: ERILIAParser extrait les données structurées d'un PDF ERILIA
`ERILIAParser.extraire()` SHALL retourner le même dict normalisé que `GDHParser`. Les champs non trouvés SHALL être `None` ou `""`. Le format ERILIA est un PDF 1 page contenant l'ensemble des données y compris les prix.

#### Scenario: Extraction complète d'un PDF ERILIA standard
- **WHEN** `ERILIAParser.extraire()` est appelé avec un PDF ERILIA valide
- **THEN** le dict retourné contient `numero_bdc`, `adresse`, `objet_travaux`, `montant_ht`, `montant_tva`, `montant_ttc`, et la liste `lignes_prestation`

#### Scenario: Extraction du numéro de marché ERILIA
- **WHEN** le PDF ERILIA contient un numéro de marché
- **THEN** `dict["numero_marche"]` contient ce numéro

#### Scenario: Extraction de la date d'émission
- **WHEN** le PDF ERILIA contient une date d'émission
- **THEN** `dict["date_emission"]` est un objet `datetime.date` au bon format

#### Scenario: Extraction des informations de contact
- **WHEN** le PDF ERILIA contient les coordonnées de l'émetteur bailleur
- **THEN** `dict["emetteur_nom"]` et `dict["emetteur_telephone"]` sont renseignés

#### Scenario: Champ absent dans le PDF
- **WHEN** un champ attendu est absent du PDF ERILIA
- **THEN** le dict retourne `""` pour ce champ (pas d'exception levée)

### Requirement: ERILIAParser détecte le marqueur d'identité ERILIA
Le parser SHALL être sélectionné par `detecter_parser()` uniquement si le texte de la première page contient un marqueur propre au format ERILIA.

#### Scenario: Détection positive ERILIA
- **WHEN** `detecter_parser()` analyse un PDF dont la page 1 contient le marqueur ERILIA
- **THEN** une instance `ERILIAParser` est retournée

#### Scenario: Détection négative (PDF non-ERILIA)
- **WHEN** `detecter_parser()` analyse un PDF sans marqueur ERILIA
- **THEN** `ERILIAParser` n'est pas retourné

### Requirement: detecter_parser lève PDFTypeInconnu si aucun format reconnu
Si le PDF ne correspond ni à GDH ni à ERILIA, `detecter_parser()` SHALL lever `PDFTypeInconnu`.

#### Scenario: PDF sans marqueur reconnu
- **WHEN** `detecter_parser()` analyse un PDF qui n'est ni GDH ni ERILIA
- **THEN** `PDFTypeInconnu` est levée avec un message descriptif
