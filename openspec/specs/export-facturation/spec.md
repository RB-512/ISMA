### Requirement: Le CDT peut exporter les BDC en facturation au format Excel
Le système SHALL fournir une vue accessible au CDT permettant de télécharger un fichier Excel (.xlsx) contenant les BDC filtrés. Le fichier SHALL contenir les colonnes : N° BDC, Bailleur, Adresse, Ville, Sous-traitant, % ST, Montant HT (€), Montant ST (€), Date réalisation, Statut.

#### Scenario: Export Excel des BDC à facturer
- **WHEN** le CDT accède à `/bdc/export/` et soumet le formulaire avec statut = A_FACTURER
- **THEN** un fichier Excel (.xlsx) est téléchargé contenant uniquement les BDC à facturer avec toutes les colonnes

#### Scenario: Export Excel des BDC facturés
- **WHEN** le CDT soumet le formulaire avec statut = FACTURE
- **THEN** un fichier Excel contenant uniquement les BDC facturés est téléchargé

#### Scenario: Export sans filtre statut
- **WHEN** le CDT soumet le formulaire sans filtre statut
- **THEN** le fichier contient les BDC à facturer ET facturés (les deux statuts pertinents)

#### Scenario: Accès réservé au CDT
- **WHEN** une secrétaire accède à `/bdc/export/`
- **THEN** l'accès est refusé (403)

### Requirement: L'export est filtrable par période de réalisation
Le système SHALL permettre de filtrer les BDC exportés par plage de dates de réalisation (date_du / date_au).

#### Scenario: Filtre par période
- **WHEN** le CDT filtre avec date_du = 2026-02-01 et date_au = 2026-02-28
- **THEN** seuls les BDC dont la date_realisation est dans cette plage sont exportés

#### Scenario: Filtre avec uniquement date de début
- **WHEN** le CDT filtre avec date_du = 2026-02-01 sans date de fin
- **THEN** les BDC dont la date_realisation est >= 2026-02-01 sont exportés

#### Scenario: Filtre avec uniquement date de fin
- **WHEN** le CDT filtre avec date_au = 2026-02-28 sans date de début
- **THEN** les BDC dont la date_realisation est <= 2026-02-28 sont exportés

### Requirement: L'export est filtrable par sous-traitant
Le système SHALL permettre de filtrer les BDC exportés par sous-traitant via un champ select.

#### Scenario: Filtre par sous-traitant
- **WHEN** le CDT sélectionne un sous-traitant dans le filtre
- **THEN** seuls les BDC attribués à ce sous-traitant sont exportés

#### Scenario: Sans filtre sous-traitant
- **WHEN** le CDT ne sélectionne aucun sous-traitant
- **THEN** les BDC de tous les sous-traitants sont exportés

### Requirement: Le formulaire d'export affiche un aperçu du nombre de BDC
Le système SHALL afficher le nombre de BDC correspondant aux filtres avant téléchargement. Si aucun BDC ne correspond, le bouton d'export SHALL être désactivé avec un message.

#### Scenario: Aperçu du compte
- **WHEN** le CDT accède à `/bdc/export/` avec des filtres
- **THEN** la page affiche "X BDC correspondent à votre sélection" et le bouton "Télécharger"

#### Scenario: Aucun résultat
- **WHEN** les filtres ne correspondent à aucun BDC
- **THEN** la page affiche "Aucun BDC ne correspond à vos critères" et le bouton est désactivé

### Requirement: Le nom du fichier exporté est descriptif
Le fichier exporté SHALL avoir un nom au format `export_facturation_YYYY-MM-DD.xlsx` avec la date du jour.

#### Scenario: Nom du fichier
- **WHEN** le CDT télécharge l'export le 28/02/2026
- **THEN** le fichier se nomme `export_facturation_2026-02-28.xlsx`

### Requirement: Colonne adresse du relevé de facturation
Le relevé de facturation DOIT afficher la ville dans l'export PDF, en plus de l'adresse.

#### Scenario: Export PDF avec ville
- **WHEN** un utilisateur exporte le relevé en PDF
- **THEN** la colonne "Ville" DOIT être présente avec la valeur du champ `ville` du BDC
