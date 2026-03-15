## ADDED Requirements

### Requirement: Envoi email attribution resilient
La fonction `envoyer_email_attribution` NE DOIT PAS propager d'exceptions. Les erreurs SMTP sont attrapees et loggees.

#### Scenario: Erreur SMTP
- **WHEN** le serveur SMTP refuse la connexion pendant `envoyer_email_attribution`
- **THEN** la fonction retourne sans lever d'exception et un log warning est emis

### Requirement: Template email tolerant aux placeholders inconnus
La fonction de rendu du template email DOIT gerer les placeholders inconnus dans le sujet ou le corps sans lever de `KeyError`.

#### Scenario: Placeholder inconnu dans le template admin
- **WHEN** l'admin a saisi `{nom_st}` dans le template ConfigEmail mais cette variable n'existe pas
- **THEN** le placeholder est rendu tel quel ou vide, sans crash
