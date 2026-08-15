## 1. App Django

- [x] 1.1 Créer l'app `apps/changelog/` (`manage.py startapp changelog` dans `apps/`, ajuster `apps.py` avec `name = "apps.changelog"`)
- [x] 1.2 Ajouter `"apps.changelog"` à `LOCAL_APPS` dans `config/settings/base.py`

## 2. Modèle

- [x] 2.1 Créer le modèle `Version` dans `apps/changelog/models.py` (`numero`, `date_mise_en_ligne`, `resume`, `changements`, `created_by`, `created_at`, `Meta.ordering`)
- [x] 2.2 Ajouter une validation de format sur `numero` (regex `^\d{4}\.\d{2}\.\d{2}(-\d+)?$`) dans `clean()` ou via un `validators=[...]`
- [x] 2.3 Générer et appliquer la migration initiale (`uv run manage.py makemigrations changelog && uv run manage.py migrate`)

## 3. Admin

- [x] 3.1 Enregistrer `Version` dans `apps/changelog/admin.py` (champs `numero`, `date_mise_en_ligne`, `resume`, `changements`, `created_by` pré-rempli sur `request.user`)

## 4. Vues et urls

- [x] 4.1 Créer la vue fonction `version_list` dans `apps/changelog/views.py` (liste paginée, `@login_required` seul, pas de restriction de groupe)
- [x] 4.2 Créer `apps/changelog/urls.py` (`app_name = "changelog"`, route `nouveautes/` → `version_list`)
- [x] 4.3 Inclure les urls de `changelog` à la racine dans `config/urls.py`

## 5. Templates

- [x] 5.1 Créer `templates/changelog/version_list.html` (étend `base.html`, réutilise les classes du design system, état vide si aucune version)

## 6. Badge sidebar

- [x] 6.1 Ajouter dans `templates/base.html`, sous le logo en en-tête de la sidebar, un badge affichant le numéro de la dernière `Version` publiée, lien vers `/nouveautes/` — absent si aucune version n'existe
- [x] 6.2 Exposer la dernière `Version` au contexte de toutes les pages (context processor dans `apps/changelog/context_processors.py`, enregistré dans `TEMPLATES` de `config/settings/base.py`) plutôt que de dupliquer la requête dans chaque vue

## 7. Tests

- [x] 7.1 Tests modèle : unicité de `numero`, validation du format CalVer
- [x] 7.2 Tests vue `version_list` : accès authentifié requis, tri par date décroissante, pagination
- [x] 7.3 Test du badge sidebar : présent avec une version publiée, absent sans version, affiche le bon numéro

## 8. Vérification manuelle

- [x] 8.1 Créer une version de test via l'admin local, vérifier son affichage sur `/nouveautes/` et le badge dans la sidebar
- [x] 8.2 Vérifier que Secrétaire et CDT voient tous les deux `/nouveautes/` et le badge (contrairement à `/erreurs/`, réservé CDT)
