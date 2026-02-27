## ADDED Requirements

### Requirement: La secrétaire peut uploader un PDF bailleur
Le système SHALL afficher un formulaire d'upload accessible uniquement aux utilisateurs du groupe Secrétaire. Le formulaire SHALL accepter uniquement les fichiers PDF (`.pdf`). La taille maximale SHALL être de 10 Mo.

#### Scenario: Upload réussi — PDF GDH détecté
- **WHEN** la secrétaire soumet un fichier PDF GDH valide
- **THEN** le système extrait les données, stocke le PDF en session et redirige vers le formulaire de création pré-rempli avec un message "PDF GDH importé avec succès"

#### Scenario: Upload réussi — PDF ERILIA détecté
- **WHEN** la secrétaire soumet un fichier PDF ERILIA valide
- **THEN** le système extrait les données, stocke le PDF en session et redirige vers le formulaire de création pré-rempli avec un message "PDF ERILIA importé avec succès"

#### Scenario: Fichier non PDF rejeté
- **WHEN** la secrétaire soumet un fichier qui n'est pas un PDF (ex : `.docx`, `.png`)
- **THEN** le système affiche une erreur de validation "Seuls les fichiers PDF sont acceptés" et ne redirige pas

#### Scenario: Type de bailleur inconnu
- **WHEN** la secrétaire soumet un PDF dont le type ne peut pas être détecté (ni GDH ni ERILIA)
- **THEN** le système affiche une erreur "Type de PDF non reconnu. Formats supportés : GDH, ERILIA" et ne redirige pas

#### Scenario: PDF corrompu ou illisible
- **WHEN** la secrétaire soumet un fichier PDF corrompu ou illisible par pdfplumber
- **THEN** le système affiche une erreur "Impossible de lire ce PDF. Vérifiez que le fichier n'est pas corrompu" et ne redirige pas

#### Scenario: Accès refusé pour un non-secrétaire
- **WHEN** un utilisateur non-secrétaire (CDT ou non authentifié) accède à la page d'upload
- **THEN** le système redirige vers la page de login (si non authentifié) ou retourne HTTP 403 (si CDT)
