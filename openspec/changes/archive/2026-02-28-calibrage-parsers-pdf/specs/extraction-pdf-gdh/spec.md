## MODIFIED Requirements

### Requirement: GDHParser extrait les données structurées d'un PDF GDH
`GDHParser.extraire()` SHALL retourner un dict normalisé avec les champs du modèle `BonDeCommande`. Les champs non trouvés SHALL être `None` ou `""` (jamais une exception). Le parser SHALL utiliser pdfplumber comme extracteur principal. Les patterns regex SHALL être calibrés sur le format réel du texte pdfplumber (en-tête multi-lignes, pas de préfixes "Adresse :" ou "Objet :").

#### Scenario: Extraction complète d'un PDF GDH standard
- **WHEN** `GDHParser.extraire()` est appelé avec un PDF GDH valide à 2 pages
- **THEN** le dict retourné contient `numero_bdc`, `adresse`, `objet_travaux`, `montant_ht`, `montant_tva`, `montant_ttc`, et `lignes_prestation` (liste vide tant que le parsing des lignes n'est pas implémenté)

#### Scenario: Extraction du numéro BDC au format GDH réel
- **WHEN** le texte pdfplumber contient `n° 450056 du 09/02/2026` dans l'en-tête
- **THEN** `dict["numero_bdc"]` vaut `"450056"`

#### Scenario: Extraction de la date d'émission depuis l'en-tête
- **WHEN** le texte pdfplumber contient `n° 450056 du 09/02/2026`
- **THEN** `dict["date_emission"]` est un `datetime.date(2026, 2, 9)`

#### Scenario: Extraction du numéro de marché
- **WHEN** le texte pdfplumber contient `Marché n° 026322-CPP-003`
- **THEN** `dict["numero_marche"]` vaut `"026322-CPP-003"`

#### Scenario: Extraction de l'objet travaux depuis l'en-tête
- **WHEN** l'en-tête contient les lignes entre "Bon de commande" et "n° ..."
- **THEN** `dict["objet_travaux"]` contient `"reprise peinture SDB suite trx faience"` (lignes jointes)

#### Scenario: Extraction de l'adresse sans préfixe
- **WHEN** le texte contient `3 Rue Francois 1er` suivi de `84000 AVIGNON`
- **THEN** `dict["adresse"]` contient `"3 Rue Francois 1er"`, `dict["code_postal"]` vaut `"84000"`, `dict["ville"]` vaut `"AVIGNON"`

#### Scenario: Extraction des informations logement en une ligne
- **WHEN** le texte contient `Habitation n° 000756 de type Type 3, Etage 1, porte 107`
- **THEN** `dict["logement_numero"]` vaut `"000756"`, `dict["logement_type"]` vaut `"Type 3"`, `dict["logement_etage"]` vaut `"1"`, `dict["logement_porte"]` vaut `"107"`

#### Scenario: Extraction du programme/résidence
- **WHEN** le texte contient `VERONESE BAT 1 ENT 1 (0023-1-1)` comme programme
- **THEN** `dict["programme_residence"]` contient `"VERONESE BAT 1 ENT 1"`

#### Scenario: Extraction de l'occupant
- **WHEN** le texte contient `Occupant actuel : MUSELLA CHRISTIANE (074143/35)`
- **THEN** `dict["occupant_nom"]` vaut `"MUSELLA CHRISTIANE"`

#### Scenario: Extraction de l'émetteur
- **WHEN** le texte contient `Emetteur : Joseph LONEGRO`
- **THEN** `dict["emetteur_nom"]` vaut `"Joseph LONEGRO"`

#### Scenario: Extraction du délai d'exécution
- **WHEN** le texte contient `Prestation à réaliser pour le 20/02/2026`
- **THEN** `dict["delai_execution"]` est un `datetime.date(2026, 2, 20)`

#### Scenario: Extraction des montants financiers au format GDH
- **WHEN** le texte contient `Total HT 167.85 €`, `Total TVA 10.00 % 16.79 €`, `Total TTC 184.64 €`
- **THEN** `dict["montant_ht"]` vaut `Decimal("167.85")`, `dict["montant_tva"]` vaut `Decimal("16.79")`, `dict["montant_ttc"]` vaut `Decimal("184.64")`

#### Scenario: Champ absent dans le PDF
- **WHEN** un champ attendu est absent du PDF GDH (ex : numéro de logement non renseigné)
- **THEN** le dict retourne `""` pour ce champ (pas d'exception levée)

#### Scenario: PDF GDH à 1 seule page (format incomplet)
- **WHEN** le PDF GDH ne contient qu'une seule page au lieu de 2
- **THEN** l'extraction réussit avec les données de la page 1, et les champs spécifiques à la page 2 sont `""`

## ADDED Requirements

### Requirement: Test d'intégration GDH avec PDF modèle réel
Le système SHALL inclure un test d'intégration qui exécute `GDHParser.extraire()` sur le fichier `docs/Modèle_bdc_GDH.pdf` et vérifie les valeurs exactes de chaque champ.

#### Scenario: Extraction du PDF modèle GDH retourne les bonnes valeurs
- **WHEN** `GDHParser("docs/Modèle_bdc_GDH.pdf").extraire()` est appelé
- **THEN** `numero_bdc` vaut `"450056"`, `date_emission` vaut `date(2026, 2, 9)`, `montant_ht` vaut `Decimal("167.85")`, `adresse` contient `"Francois 1er"`, `ville` vaut `"AVIGNON"`
