## MODIFIED Requirements

### Requirement: Vue sous-traitant dans la page attribution
Le systeme SHALL afficher un apercu de la fiche chantier (telle qu'envoyee au ST) dans l'iframe "Vue sous-traitant" de la page d'attribution. Cette fiche est generee a partir des donnees en base, pas du PDF bailleur.

#### Scenario: Apercu fiche chantier dans l'iframe
- **WHEN** le CDT clique sur "Vue sous-traitant" dans la page d'attribution
- **THEN** l'iframe affiche la fiche chantier PDF generee avec les donnees du BDC (sans prix)

#### Scenario: Fiche disponible pour tous les bailleurs
- **WHEN** le CDT ouvre la vue sous-traitant pour n'importe quel bailleur (GDH, ERILIA, etc.)
- **THEN** la fiche chantier est generee et affichee sans erreur
- **AND** aucune configuration specifique au bailleur n'est requise
