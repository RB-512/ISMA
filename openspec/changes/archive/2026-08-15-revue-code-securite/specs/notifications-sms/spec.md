## ADDED Requirements

### Requirement: Backend SMS resilient
`OvhSmsBackend.send()` NE DOIT PAS propager d'exceptions. Les erreurs HTTP et reseau sont attrapees, loggees, et la methode retourne `False`.

#### Scenario: API OVH indisponible
- **WHEN** l'API OVH retourne un code 503 ou une erreur de connexion
- **THEN** `send()` retourne `False` et un log warning est emis
