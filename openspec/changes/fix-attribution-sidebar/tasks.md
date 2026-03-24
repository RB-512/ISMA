## 1. Fix contexte sidebar

- [x] 1.1 Ajouter `"is_cdt": request.user.groups.filter(name="CDT").exists()` dans le contexte de `detail_sidebar()` (L516-526)
- [x] 1.2 Ajouter `"is_cdt": request.user.groups.filter(name="CDT").exists()` dans le contexte de `sidebar_save_and_transition()` (L623-634)

## 2. Verification

- [x] 2.1 Lancer les tests existants pour verifier la non-regression
