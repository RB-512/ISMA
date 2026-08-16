## Purpose

Répondre à la question de contrôle du CDT : pour chaque sous-traitant, où en est-on ? Un
tableau des ST ayant des BDC, comptés par statut, et le détail à un clic. C'est une lecture
de vérification — on recoupe ce que l'on croit avoir confié avec ce que la base enregistre,
typiquement avant de facturer ou face à une réclamation.

La capability est en lecture seule et réservée au CDT. Elle mène à l'export
(`export-facturation`) et aux fiches individuelles (`fiche-detail-bdc`) sans rien modifier
elle-même. Sa nature est rétrospective et comptable : elle regarde tous les statuts, y
compris les BDC déjà facturés.

## Requirements

### Requirement: Le CDT dispose d'un écran de recoupement par sous-traitant
Le système SHALL fournir un écran listant tous les sous-traitants actifs avec le nombre de BDC par statut (en cours, à facturer, facturé). Le CDT SHALL pouvoir cliquer sur un ST pour voir le détail de ses BDC. Un bouton "Exporter" SHALL être affiché, pointant vers `/bdc/export/`.

#### Scenario: Affichage de la liste des ST avec compteurs
- **WHEN** le CDT accède à `/bdc/recoupement/`
- **THEN** la page affiche un tableau avec chaque ST actif, le nombre de BDC en cours, à facturer et facturés

#### Scenario: ST sans BDC masqué
- **WHEN** un ST actif n'a aucun BDC attribué
- **THEN** il n'apparaît pas dans le tableau de recoupement

#### Scenario: Accès réservé au CDT
- **WHEN** une secrétaire accède à `/bdc/recoupement/`
- **THEN** l'accès est refusé (403)

#### Scenario: Bouton Exporter visible
- **WHEN** le CDT accède à `/bdc/recoupement/`
- **THEN** un bouton "Exporter" est affiché dans l'en-tête, pointant vers `/bdc/export/`

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
