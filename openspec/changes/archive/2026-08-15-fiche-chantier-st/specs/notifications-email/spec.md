## MODIFIED Requirements

### Requirement: Le système envoie un email avec le BDC terrain au ST lors de l'attribution
Le systeme SHALL envoyer un email au sous-traitant contenant un resume du BDC et la fiche chantier generee en piece jointe. L'email ne SHALL JAMAIS contenir de prix. La piece jointe est la fiche chantier PDF generee a partir des donnees en base (et non le PDF bailleur masque).

#### Scenario: Email envoye avec fiche chantier apres attribution
- **WHEN** le CDT attribue un BDC a un ST ayant une adresse email
- **THEN** un email est envoye au ST avec la fiche chantier PDF generee en piece jointe et un resume (numero BDC, adresse, objet travaux)

#### Scenario: Email sans piece jointe si generation fiche echoue
- **WHEN** la generation de la fiche chantier echoue
- **THEN** l'email est envoye sans piece jointe avec un message invitant le ST a recuperer le document aupres du conducteur de travaux

#### Scenario: Attribution reussie meme si email echoue
- **WHEN** l'envoi de l'email echoue
- **THEN** l'attribution du BDC est quand meme effectuee et l'erreur est loggee en warning

#### Scenario: Pas d'email si ST sans adresse email
- **WHEN** le ST attribue n'a pas d'adresse email
- **THEN** aucun email n'est envoye et un warning est logge
