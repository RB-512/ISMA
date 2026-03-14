## MODIFIED Requirements

### Requirement: Passage en facturation
Le système DOIT gérer proprement le passage en facturation même lorsque la date de prestation est antérieure à la date actuelle. Le système NE DOIT PAS produire une erreur 500.

#### Scenario: Erreur technique lors de la facturation
- **WHEN** une erreur inattendue survient lors du passage en facturation
- **THEN** le système DOIT logger l'erreur, afficher un message d'erreur à l'utilisateur, et rediriger vers la page de détail du BDC sans changer son statut
