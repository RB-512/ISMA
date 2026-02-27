## ADDED Requirements

### Requirement: GDHParser extrait les données structurées d'un PDF GDH
`GDHParser.extraire()` SHALL retourner un dict normalisé avec les champs du modèle `BonDeCommande`. Les champs non trouvés SHALL être `None` ou `""` (jamais une exception). Le parser SHALL utiliser pdfplumber comme extracteur principal.

#### Scenario: Extraction complète d'un PDF GDH standard
- **WHEN** `GDHParser.extraire()` est appelé avec un PDF GDH valide à 2 pages
- **THEN** le dict retourné contient `numero_bdc`, `adresse`, `objet_travaux`, `montant_ht`, `montant_tva`, `montant_ttc`, et la liste `lignes_prestation`

#### Scenario: Extraction du numéro BDC
- **WHEN** le PDF GDH contient un numéro de bon de commande au format GDH
- **THEN** `dict["numero_bdc"]` contient exactement ce numéro (string, sans espaces superflus)

#### Scenario: Extraction des montants financiers
- **WHEN** le PDF GDH contient les montants HT, TVA et TTC
- **THEN** `dict["montant_ht"]`, `dict["montant_tva"]`, `dict["montant_ttc"]` sont des `Decimal` avec 2 décimales

#### Scenario: Extraction des lignes de prestation
- **WHEN** le PDF GDH contient un tableau de prestations
- **THEN** `dict["lignes_prestation"]` est une liste de dicts avec les clés `designation`, `quantite`, `unite`, `prix_unitaire`, `montant`

#### Scenario: Champ absent dans le PDF
- **WHEN** un champ attendu est absent du PDF GDH (ex : numéro de logement non renseigné)
- **THEN** le dict retourne `""` pour ce champ (pas d'exception levée)

#### Scenario: PDF GDH à 1 seule page (format incomplet)
- **WHEN** le PDF GDH ne contient qu'une seule page au lieu de 2
- **THEN** l'extraction réussit avec les données de la page 1, et les champs spécifiques à la page 2 sont `""`

### Requirement: GDHParser détecte le marqueur d'identité GDH
Le parser SHALL être sélectionné par `detecter_parser()` uniquement si le texte de la première page contient un marqueur propre au format GDH (ex : mention du nom de l'organisation GDH).

#### Scenario: Détection positive GDH
- **WHEN** `detecter_parser()` analyse un PDF dont la page 1 contient le marqueur GDH
- **THEN** une instance `GDHParser` est retournée

#### Scenario: Détection négative (PDF non-GDH)
- **WHEN** `detecter_parser()` analyse un PDF sans marqueur GDH
- **THEN** `GDHParser` n'est pas retourné
