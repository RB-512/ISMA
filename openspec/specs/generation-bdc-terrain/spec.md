### Requirement: Le système génère un PDF terrain sans prix pour les BDC GDH
Pour les BDC du bailleur GDH, le système SHALL extraire la page 2 du PDF original (bon d'intervention sans prix) et la stocker comme PDF terrain. Si le PDF original n'a pas de page 2, le système SHALL lever une erreur explicite.

#### Scenario: Extraction page 2 GDH réussie
- **WHEN** `generer_pdf_terrain()` est appelé pour un BDC GDH avec un PDF original de 2 pages
- **THEN** la page 2 est extraite comme PDF séparé et stockée dans `bdc.pdf_terrain`

#### Scenario: PDF GDH sans page 2
- **WHEN** `generer_pdf_terrain()` est appelé pour un BDC GDH dont le PDF original n'a qu'une page
- **THEN** une erreur `GenerationTerrainError` est levée avec un message explicite

#### Scenario: PDF terrain ne contient pas de prix
- **WHEN** le PDF terrain GDH est généré
- **THEN** le contenu de la page extraite ne contient pas de montants (la page 2 GDH est nativement sans prix)

### Requirement: Le système génère un PDF terrain sans prix pour les BDC ERILIA
Pour les BDC du bailleur ERILIA, le système SHALL générer un PDF à partir d'un template HTML contenant les informations du BDC SANS aucun prix. Le PDF SHALL contenir : numéro BDC, adresse complète, programme/résidence, objet travaux, délai, occupant, prestations (désignation + quantité + unité, SANS prix unitaire ni montant).

#### Scenario: Génération PDF ERILIA réussie
- **WHEN** `generer_pdf_terrain()` est appelé pour un BDC ERILIA
- **THEN** un PDF est généré via WeasyPrint depuis le template HTML et stocké dans `bdc.pdf_terrain`

#### Scenario: Le PDF ERILIA ne contient aucun prix
- **WHEN** le PDF terrain ERILIA est généré pour un BDC avec `montant_ht=1071.40`, `montant_tva=107.14`, `montant_ttc=1178.54` et des lignes de prestation avec prix
- **THEN** le PDF terrain ne contient aucun montant, ni prix unitaire, ni total, ni TVA

#### Scenario: Le PDF ERILIA contient les prestations sans prix
- **WHEN** le BDC a 3 lignes de prestation (WC, cuisine, plafonds)
- **THEN** le PDF terrain affiche les 3 désignations avec quantité et unité, mais sans prix

#### Scenario: Génération ERILIA sans PDF original
- **WHEN** `generer_pdf_terrain()` est appelé pour un BDC ERILIA sans PDF original
- **THEN** le PDF terrain est quand même généré (il est construit à partir des données, pas du PDF)

### Requirement: La fonction generer_pdf_terrain dispatche selon le bailleur
`generer_pdf_terrain(bdc)` SHALL détecter le type de bailleur (via `bdc.bailleur.code`) et appeler la stratégie appropriée : extraction page 2 pour GDH, génération HTML→PDF pour ERILIA. Elle SHALL retourner le BDC avec le champ `pdf_terrain` rempli.

#### Scenario: Dispatch GDH
- **WHEN** `generer_pdf_terrain()` est appelé pour un BDC avec `bailleur.code == "GDH"`
- **THEN** la stratégie d'extraction page 2 est utilisée

#### Scenario: Dispatch ERILIA
- **WHEN** `generer_pdf_terrain()` est appelé pour un BDC avec `bailleur.code == "ERILIA"`
- **THEN** la stratégie de génération HTML→PDF est utilisée

#### Scenario: Bailleur inconnu
- **WHEN** `generer_pdf_terrain()` est appelé pour un BDC avec un code bailleur non supporté
- **THEN** la stratégie ERILIA (génération HTML) est utilisée par défaut (fonctionne pour tout bailleur)

### Requirement: Le PDF terrain est généré automatiquement lors de l'attribution
Le système SHALL générer le PDF terrain automatiquement quand un BDC est attribué via `attribuer_st()` ou réattribué via `reattribuer_st()`. Si la génération échoue, l'attribution SHALL quand même réussir (le PDF terrain est non-bloquant).

#### Scenario: Génération automatique à l'attribution
- **WHEN** `attribuer_st()` est appelé avec succès
- **THEN** `generer_pdf_terrain()` est appelé et le PDF terrain est stocké sur le BDC

#### Scenario: Régénération à la réattribution
- **WHEN** `reattribuer_st()` est appelé avec succès
- **THEN** le PDF terrain est régénéré (le nouveau ST peut nécessiter un envoi)

#### Scenario: Échec de génération non-bloquant
- **WHEN** `generer_pdf_terrain()` échoue (ex: PDF original corrompu)
- **THEN** l'attribution réussit quand même, `pdf_terrain` reste vide, un warning est loggé

### Requirement: Le modèle BonDeCommande a un champ pdf_terrain
Le modèle `BonDeCommande` SHALL avoir un champ `pdf_terrain` (FileField, nullable, blank) pour stocker le PDF terrain généré.

#### Scenario: Champ pdf_terrain disponible
- **WHEN** un BDC est créé
- **THEN** le champ `pdf_terrain` est disponible, initialement vide

#### Scenario: Stockage du PDF terrain
- **WHEN** le PDF terrain est généré
- **THEN** il est stocké dans le répertoire media `bdc_terrain/<annee>/<mois>/<numero_bdc>_terrain.pdf`

### Requirement: Le PDF terrain est téléchargeable depuis la fiche détail
Une vue `telecharger_terrain` SHALL servir le fichier PDF terrain en téléchargement. Un bouton "BDC terrain" SHALL être visible sur la fiche détail quand `pdf_terrain` est renseigné.

#### Scenario: Téléchargement du PDF terrain
- **WHEN** un utilisateur authentifié accède à `/<pk>/terrain/`
- **THEN** le fichier PDF terrain est servi en téléchargement avec le bon content-type

#### Scenario: Téléchargement sans PDF terrain
- **WHEN** un utilisateur accède à `/<pk>/terrain/` mais `pdf_terrain` est vide
- **THEN** une erreur 404 est retournée

#### Scenario: Bouton visible après attribution
- **WHEN** un utilisateur voit un BDC avec `pdf_terrain` renseigné
- **THEN** un bouton "BDC terrain" est affiché sur la fiche détail

### Requirement: Localisation sur fiche chantier sous-traitant
La fiche chantier ST DOIT afficher étage et porte en plus du numéro de logement.

#### Scenario: Logement avec étage et porte
- **WHEN** `logement_etage` et `logement_porte` sont renseignés
- **THEN** afficher "N° — Étage X / Porte Y"
