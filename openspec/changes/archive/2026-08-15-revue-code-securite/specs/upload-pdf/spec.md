## ADDED Requirements

### Requirement: Limite taille upload serveur
La vue `upload_pdf` DOIT rejeter les fichiers depassant 10 Mo cote serveur avec un message d'erreur explicite.

#### Scenario: Upload d'un PDF de 15 Mo
- **WHEN** un utilisateur uploade un fichier PDF de 15 Mo
- **THEN** le systeme affiche un message d'erreur "Fichier trop volumineux" sans traiter le fichier
