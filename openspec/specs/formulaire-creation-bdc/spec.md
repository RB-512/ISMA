## ADDED Requirements

### Requirement: Le formulaire de création est pré-rempli depuis l'extraction PDF
Le système SHALL afficher un formulaire `BonDeCommandeForm` dont les champs extraits (numéro, adresse, travaux, montants, etc.) sont pré-remplis et éditables. Les champs non extraits restent vides pour saisie manuelle.

#### Scenario: Accès au formulaire après upload réussi
- **WHEN** la secrétaire est redirigée après un upload réussi
- **THEN** le formulaire affiche les données extraites dans les champs correspondants et les champs vides pour les informations manquantes

#### Scenario: Accès direct sans upload préalable
- **WHEN** la secrétaire accède à `/bdc/nouveau/` sans avoir préalablement uploadé un PDF (session vide)
- **THEN** le système affiche le formulaire vide (création manuelle) sans message d'erreur

### Requirement: La détection de doublon bloque la création
Le système SHALL vérifier que le `numero_bdc` soumis n'existe pas déjà en base. Si un doublon est détecté, la soumission SHALL être bloquée avec un message d'erreur explicite.

#### Scenario: Numéro BDC déjà existant
- **WHEN** la secrétaire soumet un formulaire avec un `numero_bdc` déjà présent en base
- **THEN** le formulaire est réaffiché avec l'erreur "Le BDC n°[X] existe déjà dans le système" et aucun BDC n'est créé

#### Scenario: Numéro BDC unique
- **WHEN** la secrétaire soumet un formulaire avec un `numero_bdc` qui n'existe pas encore
- **THEN** aucune erreur de doublon n'est affichée

### Requirement: L'occupation est requise pour un statut À_FAIRE direct
Si la secrétaire renseigne le champ `occupation` lors de la création, le BDC est créé directement en statut `A_FAIRE`. Sans occupation, le BDC est créé en `A_TRAITER`.

#### Scenario: Création avec occupation renseignée → A_FAIRE
- **WHEN** la secrétaire soumet le formulaire avec `occupation` = "VACANT" ou "OCCUPE"
- **THEN** le BDC est créé avec statut `A_FAIRE`

#### Scenario: Création sans occupation → A_TRAITER
- **WHEN** la secrétaire soumet le formulaire sans renseigner le champ `occupation`
- **THEN** le BDC est créé avec statut `A_TRAITER`

### Requirement: La création du BDC est tracée dans l'historique
Lors de la création d'un BDC, le système SHALL créer une entrée `HistoriqueAction` avec `action=CREATION`.

#### Scenario: Trace de création enregistrée
- **WHEN** un BDC est créé avec succès
- **THEN** `HistoriqueAction.objects.filter(bdc=bdc, action="CREATION")` retourne exactement 1 entrée avec `utilisateur` = la secrétaire connectée

### Requirement: Le PDF original est stocké et accessible
Le fichier PDF uploadé SHALL être attaché au BDC créé (`pdf_original` FileField) et consultable depuis la fiche BDC.

#### Scenario: PDF stocké lors de la création
- **WHEN** un BDC est créé après upload d'un PDF
- **THEN** `bdc.pdf_original` n'est pas vide et le fichier existe dans `MEDIA_ROOT/bdc/<année>/<mois>/`

#### Scenario: Création manuelle sans PDF
- **WHEN** un BDC est créé via le formulaire vide (sans PDF uploadé)
- **THEN** `bdc.pdf_original` est vide et aucune erreur n'est levée

### Requirement: Après création, la secrétaire est redirigée vers la fiche BDC
Le système SHALL rediriger vers la page de détail du BDC nouvellement créé avec un message de succès.

#### Scenario: Redirection post-création
- **WHEN** le formulaire est soumis avec succès
- **THEN** la secrétaire est redirigée vers `/bdc/<id>/` avec le message "BDC n°[X] créé avec succès"
