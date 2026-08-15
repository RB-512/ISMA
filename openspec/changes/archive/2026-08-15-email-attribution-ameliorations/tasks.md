## 1. Toggle UI — attribution_split.html

- [x] 1.1 Etendre le `x-data` de la barre d'onglets avec `joindre: true`
- [x] 1.2 Ajouter le toggle "Joindre le BDC" a droite dans la barre d'onglets
- [x] 1.3 Conditionner la visibilite du bouton "Vue sous-traitant" avec `x-show="joindre"`
- [x] 1.4 Forcer `vueST = false` quand `joindre` passe a `false` (via `@click` ou `x-effect`)
- [x] 1.5 Ajouter `<input type="hidden" name="joindre_bdc" :value="joindre ? 'on' : ''">` dans le formulaire

## 2. Propagation de joindre_bdc dans la chaine backend

- [x] 2.1 `envoyer_email_attribution()` (email.py) : ajouter parametre `joindre_bdc=True`, conditionner l'attachement du PDF, supprimer le message fallback si `joindre_bdc=False`
- [x] 2.2 `envoyer_email_reattribution()` (email.py) : passer `joindre_bdc` a `envoyer_email_attribution()`
- [x] 2.3 `_notifier_st_si_possible()` (services.py) : ajouter parametre `joindre_bdc=True`, passer a `envoyer_email_attribution()`
- [x] 2.4 `_notifier_reattribution_si_possible()` (services.py) : meme pattern
- [x] 2.5 `attribuer_st()` (services.py) : ajouter parametre `joindre_bdc=True`, passer a `_notifier_st_si_possible()`
- [x] 2.6 `reattribuer_st()` (services.py) : meme pattern
- [x] 2.7 View `attribution_split` (views.py) : lire `joindre_bdc = request.POST.get("joindre_bdc") == "on"`, passer a `attribuer_st()` / `reattribuer_st()`

## 3. Etage et porte dans le corps du mail

- [x] 3.1 `envoyer_email_attribution()` (email.py) : ajouter `etage` et `porte` dans le dict `variables`
- [x] 3.2 Ajouter la ligne etage/porte dans le corps par defaut (uniquement si les valeurs existent)

## 4. Verification

- [x] 4.1 Lancer les tests existants pour verifier la non-regression
