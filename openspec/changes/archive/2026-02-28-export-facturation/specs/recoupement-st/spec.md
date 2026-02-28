## MODIFIED Requirements

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
