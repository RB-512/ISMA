## ADDED Requirements

### Requirement: Pas de credentials dans les templates
Les templates rendus en production NE DOIVENT PAS contenir de credentials (mots de passe, emails de test) visibles dans le HTML.

#### Scenario: Page de login en production
- **WHEN** un visiteur accede a la page de login en production
- **THEN** aucun email ni mot de passe n'est visible dans le HTML source

### Requirement: Media files authentifies en mode LAN
En mode LAN (`USE_NGINX_MEDIA = False`), les fichiers media DOIVENT etre servis uniquement aux utilisateurs authentifies.

#### Scenario: Acces media sans login en LAN
- **WHEN** un utilisateur non authentifie accede directement a une URL `/media/bdc/...`
- **THEN** le systeme redirige vers la page de login

### Requirement: XSS prevention dans les messages flash
Les messages flash contenant des donnees issues de la base de donnees DOIVENT utiliser `format_html()` au lieu de `mark_safe()` pour echapper automatiquement les valeurs interpolees.

#### Scenario: Numero BDC contenant des caracteres HTML
- **WHEN** un BDC a un `numero_bdc` contenant `<script>`
- **THEN** le caractere est echappe dans le message flash et n'est pas execute comme HTML
