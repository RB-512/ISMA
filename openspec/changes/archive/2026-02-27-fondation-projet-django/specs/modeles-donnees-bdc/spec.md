## ADDED Requirements

### Requirement: Modele Bailleur

Le systeme SHALL fournir un modele `Bailleur` avec les champs : `id` (PK auto), `nom` (CharField, unique), `code` (CharField, unique — ex: "GDH", "ERILIA").

#### Scenario: Creation d'un bailleur
- **WHEN** un bailleur est cree avec nom="Grand Delta Habitat" et code="GDH"
- **THEN** l'enregistrement est sauvegarde en base avec un id auto-genere

#### Scenario: Unicite du code bailleur
- **WHEN** un deuxieme bailleur est cree avec le meme code "GDH"
- **THEN** une erreur d'integrite est levee

### Requirement: Modele SousTraitant

Le systeme SHALL fournir un modele `SousTraitant` avec les champs : `id` (PK auto), `nom` (CharField), `telephone` (CharField), `email` (EmailField, nullable), `actif` (BooleanField, default True).

#### Scenario: Creation d'un sous-traitant actif
- **WHEN** un sous-traitant est cree avec nom="Dupont Peinture" et telephone="0612345678"
- **THEN** l'enregistrement est sauvegarde avec actif=True par defaut

#### Scenario: Desactivation d'un sous-traitant
- **WHEN** le champ actif d'un sous-traitant est mis a False
- **THEN** le sous-traitant n'est plus propose lors des attributions (verification dans les vues futures)

### Requirement: Modele BonDeCommande

Le systeme SHALL fournir un modele `BonDeCommande` avec tous les champs definis dans le PRD section 4 :
- Identification : `numero_bdc` (unique), `numero_marche`, `bailleur` (FK Bailleur), `date_emission`
- Localisation : `programme_residence`, `adresse`, `code_postal`, `ville`, `logement_numero`, `logement_type`, `logement_etage`, `logement_porte`
- Travaux : `objet_travaux` (TextField), `delai_execution` (DateField)
- Contacts : `occupant_nom`, `occupant_telephone`, `occupant_email`, `emetteur_nom`, `emetteur_telephone`
- Montants : `montant_ht` (DecimalField), `montant_tva` (DecimalField), `montant_ttc` (DecimalField)
- Infos manuelles : `occupation` (choix VACANT/OCCUPE, nullable), `modalite_acces` (TextField, nullable), `rdv_pris` (BooleanField, default False), `rdv_date` (DateTimeField, nullable), `notes` (TextField, nullable)
- Workflow : `statut` (CharField avec choix), `sous_traitant` (FK SousTraitant, nullable), `montant_st` (DecimalField, nullable), `pourcentage_st` (DecimalField, nullable)
- Fichiers : `pdf_original` (FileField)
- Meta : `cree_par` (FK User), `created_at`, `updated_at`

#### Scenario: Creation d'un BDC complet
- **WHEN** un BDC est cree avec numero_bdc="450056", bailleur=GDH et tous les champs obligatoires
- **THEN** l'enregistrement est sauvegarde avec statut initial "A_TRAITER" et created_at auto-rempli

#### Scenario: Unicite du numero de BDC
- **WHEN** un deuxieme BDC est cree avec le meme numero_bdc="450056"
- **THEN** une erreur d'integrite est levee (detection de doublon)

#### Scenario: Le champ pdf_original accepte les fichiers PDF
- **WHEN** un fichier PDF est uploade dans le champ pdf_original
- **THEN** le fichier est stocke dans le chemin `bdc/<annee>/<mois>/<nom_fichier>`

### Requirement: Workflow de statuts avec transitions autorisees

Le systeme SHALL definir 5 statuts (A_TRAITER, A_FAIRE, EN_COURS, A_FACTURER, FACTURE) et un dictionnaire de transitions autorisees conforme a ARCHITECTURE.md section 3.2.

#### Scenario: Transition valide A_TRAITER vers A_FAIRE
- **WHEN** un BDC avec statut "A_TRAITER" est transitionne vers "A_FAIRE"
- **THEN** le statut est mis a jour et un enregistrement HistoriqueAction est cree

#### Scenario: Transition invalide A_TRAITER vers EN_COURS
- **WHEN** un BDC avec statut "A_TRAITER" tente une transition vers "EN_COURS"
- **THEN** une erreur est levee et le statut reste inchange

#### Scenario: FACTURE est un etat terminal
- **WHEN** un BDC avec statut "FACTURE" tente une transition vers n'importe quel autre statut
- **THEN** une erreur est levee et le statut reste "FACTURE"

### Requirement: Modele LignePrestation

Le systeme SHALL fournir un modele `LignePrestation` avec : `bdc` (FK BonDeCommande), `designation` (TextField), `quantite` (DecimalField), `unite` (CharField), `prix_unitaire` (DecimalField), `montant` (DecimalField), `ordre` (IntegerField).

#### Scenario: Ajout de lignes de prestation a un BDC
- **WHEN** 3 lignes de prestation sont ajoutees a un BDC
- **THEN** les 3 lignes sont sauvegardees avec le bon ordre et liees au BDC

#### Scenario: Suppression en cascade
- **WHEN** un BDC est supprime
- **THEN** toutes ses lignes de prestation sont automatiquement supprimees

### Requirement: Modele HistoriqueAction

Le systeme SHALL fournir un modele `HistoriqueAction` avec : `bdc` (FK BonDeCommande), `utilisateur` (FK User), `action` (CharField avec choix : CREATION, MODIFICATION, STATUT_CHANGE, ATTRIBUTION, REATTRIBUTION, NOTIFICATION_SMS, VALIDATION, FACTURATION), `details` (JSONField, nullable), `created_at` (auto).

#### Scenario: Enregistrement d'une action de creation
- **WHEN** un BDC est cree
- **THEN** une entree HistoriqueAction est creee avec action="CREATION" et l'utilisateur courant

#### Scenario: Les details JSON contiennent les infos de transition
- **WHEN** un BDC passe de A_TRAITER a A_FAIRE
- **THEN** une entree HistoriqueAction est creee avec action="STATUT_CHANGE" et details={"ancien_statut": "A_TRAITER", "nouveau_statut": "A_FAIRE"}
