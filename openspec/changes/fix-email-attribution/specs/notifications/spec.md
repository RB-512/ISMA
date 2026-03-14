## ADDED Requirements

### Requirement: Feedback utilisateur sur echec email
Le systeme SHALL afficher un message d'avertissement a l'utilisateur si l'email de notification au sous-traitant n'a pas pu etre envoye lors de l'attribution.

#### Scenario: Email envoye avec succes
- **WHEN** un BDC est attribue a un sous-traitant ayant un email configure
- **AND** le serveur SMTP est accessible et le mot de passe correct
- **THEN** un email est envoye au sous-traitant avec le PDF masque en piece jointe
- **AND** le message flash de succes mentionne que l'email a ete envoye

#### Scenario: Echec envoi email
- **WHEN** un BDC est attribue a un sous-traitant ayant un email configure
- **AND** l'envoi SMTP echoue (mot de passe vide, serveur injoignable, etc.)
- **THEN** l'attribution est quand meme effectuee (non-bloquant)
- **AND** un message flash d'avertissement informe l'utilisateur que l'email n'a pas pu etre envoye

#### Scenario: Sous-traitant sans email
- **WHEN** un BDC est attribue a un sous-traitant sans adresse email
- **THEN** l'attribution est effectuee normalement
- **AND** aucune tentative d'envoi email n'est faite
