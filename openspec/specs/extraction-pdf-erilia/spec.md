## ADDED Requirements

### Requirement: ERILIAParser extrait les données structurées d'un PDF ERILIA
`ERILIAParser.extraire()` SHALL retourner le même dict normalisé que `GDHParser`. Les champs non trouvés SHALL être `None` ou `""`. Le format ERILIA est un PDF 2 pages contenant l'ensemble des données y compris les prix. Les patterns regex SHALL être calibrés sur le format réel du texte pdfplumber (labels en majuscules, date sur page 2).

#### Scenario: Extraction complète d'un PDF ERILIA standard
- **WHEN** `ERILIAParser.extraire()` est appelé avec un PDF ERILIA valide
- **THEN** le dict retourné contient `numero_bdc`, `adresse`, `objet_travaux`, `montant_ht`, `montant_tva`, `montant_ttc`, et `lignes_prestation` (liste vide tant que le parsing des lignes n'est pas implémenté)

#### Scenario: Extraction du numéro BDC au format ERILIA réel
- **WHEN** le texte pdfplumber contient `ERILIA N° 2026 20205`
- **THEN** `dict["numero_bdc"]` vaut `"2026 20205"`

#### Scenario: Extraction du numéro de marché ERILIA
- **WHEN** le texte contient `Marché n° 2025 356 4 1`
- **THEN** `dict["numero_marche"]` contient `"2025 356 4 1"`

#### Scenario: Extraction de la date d'émission depuis page 2
- **WHEN** le texte pdfplumber contient `Édité le\n06-02-2026`
- **THEN** `dict["date_emission"]` est un `datetime.date(2026, 2, 6)`

#### Scenario: Extraction de l'objet travaux ERILIA
- **WHEN** le texte contient `Récl. Tech. n° 2026/15635` comme objet
- **THEN** `dict["objet_travaux"]` contient `"Récl. Tech. n° 2026/15635"`

#### Scenario: Extraction de l'adresse au format ERILIA
- **WHEN** le texte contient `ADRESSE 5 RUE DE LA PETITE VITESSE\n84000 AVIGNON`
- **THEN** `dict["adresse"]` contient `"5 RUE DE LA PETITE VITESSE"`, `dict["code_postal"]` vaut `"84000"`, `dict["ville"]` vaut `"AVIGNON"`

#### Scenario: Extraction du programme ERILIA
- **WHEN** le texte contient `Programme 1398 LES TERRASSES DE MERCURE`
- **THEN** `dict["programme_residence"]` contient `"1398 LES TERRASSES DE MERCURE"`

#### Scenario: Extraction des informations de contact émetteur
- **WHEN** le texte contient `ÉMETTEUR ARCQ GWENAEL Tél 0432743295`
- **THEN** `dict["emetteur_nom"]` vaut `"ARCQ GWENAEL"` et `dict["emetteur_telephone"]` vaut `"0432743295"`

#### Scenario: Extraction du délai d'exécution ERILIA
- **WHEN** le texte contient `PÉRIODE DU 06-02-2026 AU 15-02-2026`
- **THEN** `dict["delai_execution"]` est un `datetime.date(2026, 2, 15)` (date de fin)

#### Scenario: Extraction des informations logement structurées
- **WHEN** le texte contient les champs Étage, Logement, etc.
- **THEN** `dict["logement_etage"]` et `dict["logement_numero"]` sont extraits des champs structurés ERILIA

#### Scenario: Extraction des montants financiers au format ERILIA
- **WHEN** le texte contient `TOTAL H.T. 1.071,40`, `T.V.A. 10,00 % 107,14`, `TOTAL T.T.C. 1.178,54`
- **THEN** `dict["montant_ht"]` vaut `Decimal("1071.40")`, `dict["montant_tva"]` vaut `Decimal("107.14")`, `dict["montant_ttc"]` vaut `Decimal("1178.54")`

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

### Requirement: Test d'intégration ERILIA avec PDF modèle réel
Le système SHALL inclure un test d'intégration qui exécute `ERILIAParser.extraire()` sur le fichier `docs/Modèle_bdc_ERILIA.pdf` et vérifie les valeurs exactes de chaque champ.

#### Scenario: Extraction du PDF modèle ERILIA retourne les bonnes valeurs
- **WHEN** `ERILIAParser("docs/Modèle_bdc_ERILIA.pdf").extraire()` est appelé
- **THEN** `numero_bdc` vaut `"2026 20205"`, `date_emission` vaut `date(2026, 2, 6)`, `montant_ht` vaut `Decimal("1071.40")`, `adresse` contient `"PETITE VITESSE"`, `ville` vaut `"AVIGNON"`

### Requirement: ERILIAParser extrait les lignes de prestation depuis la table PDF
`ERILIAParser.extraire()` SHALL retourner dans `lignes_prestation` une liste de dicts contenant les champs `code`, `designation`, `unite`, `quantite`, `prix_unitaire`, `montant_ht`. Chaque dict correspond à une ligne de prestation extraite depuis la table 1 de la page 1. Les lignes de continuation de désignation SHALL être concaténées. Les lignes commençant par `EDL :` SHALL être ignorées.

#### Scenario: Extraction de 3 lignes de prestation ERILIA
- **WHEN** la table page 1 contient les articles PP4-31, PP4-33, PP4-43
- **THEN** `lignes_prestation` contient 3 dicts avec les codes respectifs `"PP4-31"`, `"PP4-33"`, `"PP4-43"`

#### Scenario: Extraction des valeurs d'une ligne ERILIA
- **WHEN** la table contient `PP4-31 Peinture finition A sur murs, plafond, FOR 1,00 180,27 198,30`
- **THEN** `lignes_prestation[0]` contient `code` vaut `"PP4-31"`, `designation` contenant `"Peinture finition A sur murs, plafond, boiseries et métalleries - WC"`, `unite` vaut `"FOR"`, `quantite` vaut `Decimal("1.00")`, `prix_unitaire` vaut `Decimal("180.27")`, `montant_ht` vaut `Decimal("180.27")`

#### Scenario: Concaténation des lignes de continuation ERILIA
- **WHEN** une ligne de prestation est suivie par `boiseries et métalleries - WC`
- **THEN** ce texte est concaténé à la `designation` de la ligne précédente

#### Scenario: Lignes EDL ignorées
- **WHEN** une ligne commence par `EDL :` dans la cellule de table
- **THEN** elle est ignorée et non ajoutée aux lignes de prestation ni concaténée à la désignation

#### Scenario: Table sans lignes de prestation identifiables
- **WHEN** la table page 1 ne contient aucune row matchant le pattern ERILIA
- **THEN** `lignes_prestation` est une liste vide `[]`

#### Scenario: Champ ordre incrémenté par ligne
- **WHEN** la table contient N lignes de prestation
- **THEN** chaque dict a un champ `ordre` allant de `0` à `N-1`

### Requirement: Test d'intégration ERILIA vérifie les lignes de prestation
Le test d'intégration sur `docs/Modèle_bdc_ERILIA.pdf` SHALL vérifier les lignes de prestation extraites.

#### Scenario: Extraction du PDF modèle ERILIA retourne les lignes correctes
- **WHEN** `ERILIAParser("docs/Modèle_bdc_ERILIA.pdf").extraire()` est appelé
- **THEN** `lignes_prestation` contient 3 lignes, avec `lignes_prestation[0]["code"]` vaut `"PP4-31"`, `lignes_prestation[0]["prix_unitaire"]` vaut `Decimal("180.27")`, `lignes_prestation[2]["code"]` vaut `"PP4-43"`, `lignes_prestation[2]["montant_ht"]` vaut `Decimal("578.03")`
