## 1. Dependance et template

- [x] 1.1 Ajouter WeasyPrint au pyproject.toml et uv sync
- [x] 1.2 Creer le template `templates/bdc/fiche_chantier_st.html` (HTML/CSS inline pour PDF) avec : numero BDC, bailleur, adresse, residence, occupation, occupant, prestations sans prix, consignes CDT, RDV, delai

## 2. Service de generation

- [x] 2.1 Creer `apps/bdc/fiche_chantier.py` avec `generer_fiche_chantier(bdc) -> bytes` qui rend le template et convertit en PDF via WeasyPrint
- [x] 2.2 Gerer les donnees partielles (sections omises si vides)

## 3. Integration vue ST

- [x] 3.1 Modifier `pdf_masque_preview` dans views.py pour appeler `generer_fiche_chantier()` au lieu de `generer_pdf_masque()`
- [x] 3.2 Verifier que l'iframe "Vue sous-traitant" dans attribution_split.html fonctionne avec la fiche generee

## 4. Integration email

- [x] 4.1 Modifier `_obtenir_pdf_masque()` dans `apps/notifications/email.py` pour utiliser `generer_fiche_chantier()` au lieu du masquage PDF
- [x] 4.2 Renommer la fonction en `_obtenir_fiche_chantier()` pour clarte

## 5. Nettoyage

- [x] 5.1 Supprimer `apps/bdc/masquage_pdf.py`
- [x] 5.2 Supprimer les imports de masquage_pdf dans les autres fichiers

## 6. Verification

- [x] 6.1 Tester la "Vue sous-traitant" sur un BDC GDH (plus de 500)
- [x] 6.2 Tester l'attribution avec envoi email et verifier la piece jointe fiche chantier
- [x] 6.3 Deployer sur le VPS et valider en production
