## ADDED Requirements

### Requirement: Toutes les vues sidebar transmettent is_cdt
Toutes les vues rendant `_detail_sidebar.html` DOIVENT passer `is_cdt` dans le contexte du template afin que le bouton d'attribution soit actif pour les CDT.

#### Scenario: CDT ouvre la sidebar sur un BDC a attribuer
- **WHEN** un utilisateur CDT clique sur un BDC au statut A_FAIRE dans le dashboard
- **THEN** le bouton "Attribuer" est vert et cliquable (lien vers attribution_split)

#### Scenario: Non-CDT ouvre la sidebar sur un BDC a attribuer
- **WHEN** un utilisateur non-CDT clique sur un BDC au statut A_FAIRE dans le dashboard
- **THEN** le bouton "Attribuer" est grise et non cliquable
