## ADDED Requirements

### Requirement: Creation BDC atomique
La creation d'un BDC (save du BDC + creation des lignes de prestation + attachement PDF) DOIT s'executer dans une transaction atomique. En cas d'echec partiel, rien n'est persiste.

#### Scenario: Erreur sur une ligne de prestation
- **WHEN** la conversion Decimal d'une ligne de prestation echoue apres que le BDC a ete sauve
- **THEN** le BDC n'est pas cree en base et l'utilisateur voit un message d'erreur

### Requirement: Parse forfait resilient
La fonction `_parse_lignes_forfait` DOIT gerer les valeurs invalides dans les champs quantite et prix unitaire sans lever d'exception non geree.

#### Scenario: Quantite non-numerique dans le formulaire forfait
- **WHEN** un utilisateur soumet une ligne forfait avec `quantite = "abc"`
- **THEN** la ligne est ignoree ou un message d'erreur est affiche, sans erreur 500
