## ADDED Requirements

### Requirement: Le système envoie un email avec le BDC terrain au ST lors de l'attribution
Le système SHALL envoyer un email au sous-traitant contenant un résumé du BDC et le PDF terrain en pièce jointe. L'email ne SHALL JAMAIS contenir de prix.

#### Scenario: Email envoyé avec PDF terrain après attribution
- **WHEN** le CDT attribue un BDC à un ST ayant une adresse email
- **THEN** un email est envoyé au ST avec le PDF terrain en pièce jointe et un résumé (numéro BDC, adresse, objet travaux)

#### Scenario: Email sans pièce jointe si PDF terrain indisponible
- **WHEN** la génération du PDF terrain échoue
- **THEN** l'email est envoyé sans pièce jointe avec un message invitant le ST à récupérer le document dans l'application

#### Scenario: Attribution réussie même si email échoue
- **WHEN** l'envoi de l'email échoue
- **THEN** l'attribution du BDC est quand même effectuée et l'erreur est loggée en warning

#### Scenario: Pas d'email si ST sans adresse email
- **WHEN** le ST attribué n'a pas d'adresse email
- **THEN** aucun email n'est envoyé et un warning est loggé

### Requirement: Le système envoie un email lors de la réattribution
Le système SHALL envoyer un email d'annulation à l'ancien ST et un email d'attribution au nouveau ST lors d'une réattribution.

#### Scenario: Email envoyé aux deux ST lors de réattribution
- **WHEN** le CDT réattribue un BDC de ST-A vers ST-B
- **THEN** un email d'annulation est envoyé à ST-A (si email renseigné) et un email d'attribution avec PDF est envoyé à ST-B (si email renseigné)
