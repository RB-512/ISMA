## 1. Calibrage GDHParser

- [x] 1.1 Réécrire `_extraire_numero_bdc` : pattern `r"n[°o]\s+(\d+)\s+du\s+"` pour matcher "n° 450056 du 09/02/2026"
- [x] 1.2 Réécrire `date_emission` : extraire la date depuis `r"du\s+(\d{2}/\d{2}/\d{4})"` dans l'en-tête
- [x] 1.3 Réécrire `numero_marche` : pattern `r"March[eé]\s+n[°o]\s+(.+?)(?:\n|$)"` pour "Marché n° 026322-CPP-003"
- [x] 1.4 Réécrire `objet_travaux` : extraire les lignes entre "Bon de commande" et "n° ..." dans l'en-tête
- [x] 1.5 Réécrire `adresse` + `code_postal` + `ville` : parser l'adresse dans le texte brut (pas de préfixe "Adresse :")
- [x] 1.6 Réécrire extraction Habitation : un seul regex pour "Habitation n° 000756 de type Type 3, Etage 1, porte 107" → logement_numero, logement_type, logement_etage, logement_porte
- [x] 1.7 Réécrire `programme_residence` : extraire le nom de programme/résidence sans préfixe "Programme :"
- [x] 1.8 Réécrire `occupant_nom` : pattern `r"Occupant actuel\s*:\s*(.+?)(?:\(|$)"` pour "Occupant actuel : MUSELLA CHRISTIANE (074143/35)"
- [x] 1.9 Réécrire `emetteur_nom` : pattern `r"Emetteur\s*:\s*(.+?)(?:\n|$)"` pour "Emetteur : Joseph LONEGRO"
- [x] 1.10 Réécrire `delai_execution` : pattern `r"[Pp]restation\s+[àa]\s+r[ée]aliser\s+pour\s+le\s+(\d{2}/\d{2}/\d{4})"`
- [x] 1.11 Réécrire `montant_ht/tva/ttc` : patterns pour "Total HT 167.85 €", "Total TVA 10.00 % 16.79 €", "Total TTC 184.64 €"
- [x] 1.12 Mettre `_extraire_lignes` à retourner `[]` (désactivé temporairement, parsing textuel dans SPEC futur)
- [x] 1.13 Mettre à jour le docstring de la classe

## 2. Calibrage ERILIAParser

- [x] 2.1 Réécrire `_extraire_numero_bdc` : pattern pour "ERILIA N° 2026 20205" → "2026 20205"
- [x] 2.2 Réécrire `date_emission` : pattern `r"[Éé]dit[ée]\s+le\s*\n?\s*(\d{2}-\d{2}-\d{4})"` pour "Édité le\n06-02-2026"
- [x] 2.3 Réécrire `numero_marche` : pattern pour "Marché n° 2025 356 4 1"
- [x] 2.4 Réécrire `objet_travaux` : extraire la réclamation technique (ex: "Récl. Tech. n° 2026/15635")
- [x] 2.5 Réécrire `adresse` : pattern `r"ADRESSE\s+(.+?)(?:\n|$)"` pour "ADRESSE 5 RUE DE LA PETITE VITESSE"
- [x] 2.6 Réécrire `programme_residence` : pattern `r"Programme\s+(.+?)(?:\n|$)"` pour "Programme 1398 LES TERRASSES DE MERCURE"
- [x] 2.7 Réécrire `emetteur_nom` + `emetteur_telephone` : parser "ÉMETTEUR ARCQ GWENAEL Tél 0432743295"
- [x] 2.8 Réécrire `delai_execution` : pattern pour "PÉRIODE DU 06-02-2026 AU 15-02-2026" → date de fin
- [x] 2.9 Réécrire extraction logement : parser les champs structurés Étage/Logement du format ERILIA
- [x] 2.10 Réécrire `montant_ht/tva/ttc` : patterns pour "TOTAL H.T. 1.071,40", "T.V.A. 10,00 % 107,14", "TOTAL T.T.C. 1.178,54"
- [x] 2.11 Mettre `_extraire_lignes` à retourner `[]` (désactivé temporairement)
- [x] 2.12 Corriger le docstring : "1 page" → "2 pages"

## 3. Tests d'intégration avec vrais PDFs

- [x] 3.1 Créer `tests/test_bdc/test_gdh_parser_integration.py` avec test sur `docs/Modèle_bdc_GDH.pdf` vérifiant chaque champ extrait
- [x] 3.2 Créer `tests/test_bdc/test_erilia_parser_integration.py` avec test sur `docs/Modèle_bdc_ERILIA.pdf` vérifiant chaque champ extrait

## 4. Mise à jour tests unitaires existants

- [x] 4.1 Adapter `test_gdh_parser.py` : mettre à jour les mocks de texte pdfplumber pour utiliser le vrai format GDH
- [x] 4.2 Adapter `test_erilia_parser.py` : mettre à jour les mocks de texte pdfplumber pour utiliser le vrai format ERILIA

## 5. Validation finale

- [x] 5.1 Exécuter `pytest` — tous les tests passent (anciens + nouveaux)
- [x] 5.2 Exécuter `ruff check` — aucune erreur de lint
