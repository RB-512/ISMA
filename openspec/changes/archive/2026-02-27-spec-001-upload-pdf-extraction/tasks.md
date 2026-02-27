## 1. Détecteur et base parsers

- [x] 1.1 Implémenter `detecter_parser()` dans `detector.py` : lire le texte de la page 1 avec pdfplumber, retourner `GDHParser` si marqueur GDH trouvé, `ERILIAParser` si marqueur ERILIA, sinon lever `PDFTypeInconnu`
- [x] 1.2 Définir les marqueurs de détection (constantes) dans `detector.py` pour GDH et ERILIA
- [x] 1.3 Écrire les tests unitaires de `detecter_parser()` : détection GDH, détection ERILIA, PDF inconnu

## 2. GDHParser

- [x] 2.1 Implémenter `GDHParser.extraire()` : ouvrir le PDF avec pdfplumber, extraire le texte des pages 1 et 2
- [x] 2.2 Parser le numéro BDC, numéro marché, date d'émission depuis le texte GDH (regex)
- [x] 2.3 Parser les champs de localisation (adresse, code postal, ville, logement, étage, porte) depuis la page 1
- [x] 2.4 Parser l'objet des travaux et le délai d'exécution depuis la page 1
- [x] 2.5 Parser les montants HT, TVA, TTC et les convertir en `Decimal`
- [x] 2.6 Parser les lignes de prestation (tableau) depuis la page 1 avec pdfplumber `extract_tables()`
- [x] 2.7 Parser les informations de contact (occupant, émetteur) depuis la page 2 si disponible
- [x] 2.8 Retourner un dict normalisé avec tous les champs du modèle `BonDeCommande` + clé `lignes_prestation`
- [x] 2.9 Écrire les tests unitaires de `GDHParser` avec fixtures PDF (ou données mockées) : extraction complète, champ absent, PDF 1 page

## 3. ERILIAParser

- [x] 3.1 Implémenter `ERILIAParser.extraire()` : ouvrir le PDF avec pdfplumber, extraire le texte de la page 1
- [x] 3.2 Parser le numéro BDC, numéro marché, date d'émission depuis le format ERILIA (regex)
- [x] 3.3 Parser les champs de localisation depuis le format ERILIA
- [x] 3.4 Parser l'objet des travaux depuis le format ERILIA
- [x] 3.5 Parser les montants HT, TVA, TTC et les convertir en `Decimal`
- [x] 3.6 Parser les lignes de prestation depuis le tableau ERILIA
- [x] 3.7 Parser les informations de contact émetteur depuis le format ERILIA
- [x] 3.8 Retourner un dict normalisé identique à `GDHParser` (même structure de clés)
- [x] 3.9 Écrire les tests unitaires de `ERILIAParser` avec fixtures PDF (ou données mockées)

## 4. URLs et vue upload

- [x] 4.1 Créer `apps/bdc/urls.py` avec les routes `upload/` et `nouveau/` et les nommer `bdc:upload` et `bdc:nouveau`
- [x] 4.2 Connecter `apps/bdc/urls.py` dans `config/urls.py` sous le préfixe `bdc/`
- [x] 4.3 Créer la vue `upload_pdf` (POST uniquement) dans `apps/bdc/views.py` avec `@group_required("Secretaire")`
- [x] 4.4 Dans `upload_pdf` : valider l'extension `.pdf` du fichier uploadé (retourner erreur si non-PDF)
- [x] 4.5 Dans `upload_pdf` : appeler `detecter_parser()` + `parser.extraire()` dans un try/except (PDFTypeInconnu, Exception)
- [x] 4.6 Dans `upload_pdf` : stocker le dict extrait + le fichier en session (`request.session["bdc_extrait"]`, `request.session["bdc_pdf_name"]`)
- [x] 4.7 Dans `upload_pdf` : rediriger vers `bdc:nouveau` avec message de succès sur réussite, réafficher le form avec erreur sinon
- [x] 4.8 Créer le template `templates/bdc/upload.html` : formulaire d'upload (enctype multipart), champ fichier, bouton soumettre, affichage des messages d'erreur
- [x] 4.9 Écrire les tests de la vue `upload_pdf` : upload valide GDH, upload valide ERILIA, fichier non PDF, PDF inconnu, accès non-secrétaire

## 5. Formulaire et vue création BDC

- [x] 5.1 Créer `apps/bdc/forms.py` avec `BonDeCommandeForm` (ModelForm basé sur `BonDeCommande`)
- [x] 5.2 Inclure tous les champs du BDC dans le formulaire (identification, localisation, travaux, contacts, occupation, accès, RDV, notes)
- [x] 5.3 Exclure les champs gérés automatiquement : `statut`, `cree_par`, `pdf_original`, `created_at`, `updated_at`
- [x] 5.4 Implémenter `clean_numero_bdc()` : lever `ValidationError` si `BonDeCommande.objects.filter(numero_bdc=...)` existe déjà
- [x] 5.5 Créer la vue `creer_bdc` (GET/POST) dans `apps/bdc/views.py` avec `@group_required("Secretaire")`
- [x] 5.6 Dans `creer_bdc` GET : lire `request.session["bdc_extrait"]` pour pré-remplir le formulaire (initial data), passer aussi les lignes de prestation au contexte
- [x] 5.7 Dans `creer_bdc` POST : valider le formulaire, créer `BonDeCommande` avec `cree_par=request.user`
- [x] 5.8 Dans `creer_bdc` POST : si `occupation` renseigné, appeler `changer_statut(bdc, A_FAIRE, user)` juste après création
- [x] 5.9 Dans `creer_bdc` POST : sauvegarder le PDF depuis la session dans `bdc.pdf_original` si disponible
- [x] 5.10 Dans `creer_bdc` POST : créer les `LignePrestation` depuis `session["bdc_extrait"]["lignes_prestation"]`
- [x] 5.11 Dans `creer_bdc` POST : appeler `enregistrer_action(bdc, user, ActionChoices.CREATION)` et vider la session
- [x] 5.12 Dans `creer_bdc` POST : rediriger vers la fiche BDC avec `messages.success("BDC n°X créé avec succès")`
- [x] 5.13 Créer le template `templates/bdc/creer_bdc.html` : formulaire pré-rempli, champs groupés par section, affichage des erreurs de validation

## 6. Vue détail BDC (stub minimal)

- [x] 6.1 Créer une vue `detail_bdc` minimale dans `apps/bdc/views.py` accessible à tous les utilisateurs authentifiés
- [x] 6.2 Ajouter la route `<int:pk>/` → `bdc:detail` dans `apps/bdc/urls.py`
- [x] 6.3 Créer le template `templates/bdc/detail.html` : affiche le numéro BDC, bailleur, statut, adresse, lien PDF si disponible

## 7. Tests d'intégration

- [x] 7.1 Écrire le test du flux complet : upload PDF → formulaire pré-rempli → soumission → BDC créé en A_TRAITER
- [x] 7.2 Écrire le test du flux complet avec occupation : upload → formulaire avec occupation → BDC créé en A_FAIRE
- [x] 7.3 Écrire le test de doublon : tentative de création avec numero_bdc existant → erreur de validation
- [x] 7.4 Écrire le test d'historique : après création, `HistoriqueAction` CREATION existe pour le BDC
- [x] 7.5 Écrire le test de l'accès CDT refusé sur `/bdc/upload/` et `/bdc/nouveau/`

## 8. Vérification finale

- [x] 8.1 Lancer `pytest` et vérifier que tous les tests passent (0 erreur, 0 warning)
- [x] 8.2 Lancer `ruff check apps/bdc/ apps/pdf_extraction/` et corriger les éventuelles erreurs
- [ ] 8.3 Vérifier manuellement le flow upload → création dans le navigateur avec un PDF réel
