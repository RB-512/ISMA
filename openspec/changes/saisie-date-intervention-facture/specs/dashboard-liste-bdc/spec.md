## ADDED Requirements

### Requirement: Le dashboard affiche la date d'intervention et la facture
La liste des BDC du tableau de bord SHALL afficher une colonne « Intervention » (date d'intervention au format jj/mm/aaaa) et une colonne « Facture » (n° de facture et date de facturation). Une information absente SHALL être affichée « — ».

#### Scenario: BDC facturé
- **WHEN** un BDC FACTURE a une date d'intervention, un n° et une date de facture
- **THEN** sa ligne affiche la date d'intervention, le n° de facture et la date de facturation

#### Scenario: BDC non encore réalisé
- **WHEN** un BDC n'a ni date d'intervention ni facture
- **THEN** les colonnes « Intervention » et « Facture » affichent « — »
