## ADDED Requirements

### Requirement: Le CDT dispose d'un écran de recoupement par sous-traitant
Le système SHALL fournir un écran listant tous les sous-traitants actifs avec le nombre de BDC par statut (en cours, à facturer, facturé). Le CDT SHALL pouvoir cliquer sur un ST pour voir le détail de ses BDC.

#### Scenario: Affichage de la liste des ST avec compteurs
- **WHEN** le CDT accède à `/bdc/recoupement/`
- **THEN** la page affiche un tableau avec chaque ST actif, le nombre de BDC en cours, à facturer et facturés

#### Scenario: ST sans BDC masqué
- **WHEN** un ST actif n'a aucun BDC attribué
- **THEN** il n'apparaît pas dans le tableau de recoupement

#### Scenario: Accès réservé au CDT
- **WHEN** une secrétaire accède à `/bdc/recoupement/`
- **THEN** l'accès est refusé (403)

### Requirement: Le CDT peut voir le détail des BDC d'un sous-traitant
Le système SHALL afficher la liste des BDC d'un ST donné, filtrables par statut (en cours, à facturer, facturé). Chaque BDC SHALL afficher : numéro, adresse, statut, date d'attribution, date de réalisation (si renseignée).

#### Scenario: Affichage des BDC d'un ST
- **WHEN** le CDT accède à `/bdc/recoupement/<st_pk>/`
- **THEN** la page affiche tous les BDC attribués à ce ST avec numéro, adresse, statut, dates

#### Scenario: Filtre par statut
- **WHEN** le CDT filtre par statut "À facturer"
- **THEN** seuls les BDC A_FACTURER du ST sont affichés

#### Scenario: Lien vers la fiche détail
- **WHEN** le CDT clique sur un numéro de BDC
- **THEN** il est redirigé vers la fiche détail du BDC
