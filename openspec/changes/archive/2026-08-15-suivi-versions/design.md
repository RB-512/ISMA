## Context

L'app dispose déjà d'un dashboard "méta" comparable : `/erreurs/` (app `apps/monitoring/`), construit récemment pour tracer les erreurs 500 en prod. Son architecture — un modèle unique simple, des vues fonctions, des urls namespacées, des templates étendant `base.html` — est directement réutilisable pour un dashboard de versions, à ceci près que `/erreurs/` est réservé au groupe CDT (`@group_required("CDT")`) alors que le suivi de version doit être visible par tous les utilisateurs authentifiés.

Le dépôt utilise aussi `HistoriqueAction` (`apps/bdc/models.py`) comme patron de journal append-only (horodaté, `TextChoices` pour le type d'action, `JSONField` pour le détail libre) — c'est la forme retenue pour le modèle `Version`.

Aucun mécanisme de version n'existe aujourd'hui : `pyproject.toml` contient `version = "0.1.0"` mais n'est lu par aucun code, `scripts/deploy.sh` ne pose ni tag ni marqueur de commit, et `templates/base.html` n'a pas de zone de pied de page.

## Goals / Non-Goals

**Goals:**
- Permettre de publier une version (numéro, date, résumé, liste de changements) en quelques clics, au moment de déployer un lot de travail.
- Rendre cette information consultable par tous les utilisateurs de l'app, sans avoir à regarder GitHub ou les logs serveur.
- Rester cohérent avec les patrons déjà en place dans le code (`apps/monitoring/`, `HistoriqueAction`).

**Non-Goals:**
- Ne pas automatiser la détection de version depuis git (pas de tag, pas de lecture de `.git` au runtime) — hors scope pour cette V1.
- Ne pas construire de formulaire de création dédié : l'admin Django suffit pour publier une version, vu la fréquence "à la demande" attendue.
- Ne pas lier automatiquement une `Version` aux changes OpenSpec archivés (voir Open Questions) — le champ `changements` reste une saisie libre en V1.

## Decisions

### Modèle unique `Version`, dans une nouvelle app `apps/changelog/`
```python
class Version(models.Model):
    numero = models.CharField(max_length=20, unique=True)      # "2026.08.15", ou "2026.08.15-2"
    date_mise_en_ligne = models.DateField()
    resume = models.TextField()                                  # ton "Nouveautés", grand public
    changements = models.JSONField(default=list)                 # ex: [{"titre": "...", "description": "..."}]
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_mise_en_ligne", "-created_at"]
```
Une app dédiée plutôt que d'étendre `apps/monitoring/` : l'audience diffère (tous les utilisateurs vs CDT uniquement pour les erreurs), donc les permissions et la vocation ne sont pas les mêmes — mieux vaut deux apps à responsabilité unique que d'introduire une distinction d'accès interne à `monitoring`.

### Numérotation CalVer par date, calculée à la création
Format `AAAA.MM.JJ`, avec suffixe `-N` si plusieurs versions le même jour. Alternative envisagée : SemVer (`v1.4.0`) — écarté car il demande de juger l'ampleur du changement à chaque publication, sans lien direct avec la date de mise en ligne que l'utilisateur veut afficher en premier lieu.

### Base de données comme unique source de vérité (pas de tag git)
Alternative envisagée : faire poser un tag git par `deploy.sh` au moment du déploiement, ou lire `git rev-parse HEAD` au runtime pour afficher un identifiant de commit. Écarté pour la V1 car :
- ça couple le déploiement à cette fonctionnalité (modification de `deploy.sh`, risque sur le pilier "process de déploiement" encore en discussion) ;
- lire `.git` au runtime suppose que le dossier soit présent dans l'image Docker de prod, ce qui n'est pas vérifié aujourd'hui.
La création d'un enregistrement `Version` reste un geste manuel, volontairement découplé du pipeline de déploiement.

### Création via l'admin Django (pas de formulaire dédié)
Cohérent avec le rythme "à la demande" — la fréquence de publication ne justifie pas de construire une UI de saisie dédiée pour l'instant. `admin.py` enregistre `Version` avec les champs `numero`, `date_mise_en_ligne`, `resume`, `changements`, `created_by` (pré-rempli sur `request.user`).

### Vues et gabarit repris de `apps/monitoring/`
- `views.py` : une vue fonction `version_list` (liste paginée), pas de vue détail nécessaire (le contenu tient dans la liste).
- `urls.py` : namespace `changelog`, route `nouveautes/`, montée à la racine dans `config/urls.py`.
- `templates/changelog/version_list.html` : étend `base.html`, réutilise les classes CSS-variables du design system déjà en place (`--color-surface-card`, etc.).
- Accès : `@login_required` seul (pas de `@group_required`) — différence assumée par rapport à `/erreurs/`.

### Badge de version dans la sidebar
Nouvelle zone dans `templates/base.html`, sous le logo (en-tête de la sidebar, lignes ~156-163 actuellement) — pas de pied de page existant où l'insérer autrement. Le badge affiche le `numero` de la dernière `Version` publiée (ou rien si aucune n'existe encore) et fait lien vers `/nouveautes/`.

## Risks / Trade-offs

- **[Risque] La création manuelle d'une `Version` est oubliée après un déploiement** → Mitigation : pas de véritable garde-fou en V1 ; si ça devient un problème récurrent, ajouter un rappel dans le processus de déploiement (pilier 3, à traiter séparément).
- **[Risque] Doublon d'information entre les `proposal.md` archivés et le champ `changements` d'une `Version`** → Mitigation : accepté pour la V1 (saisie libre) ; piste d'automatisation notée en Open Questions plutôt que résolue maintenant.
- **[Risque] `numero` unique mais généré manuellement peut créer des collisions ou erreurs de format** → Mitigation : contrainte `unique=True` en base fait échouer la création en cas de doublon exact ; la validation de format (regex `AAAA.MM.JJ(-N)?`) peut être ajoutée dans `clean()` du modèle au moment de l'implémentation.

## Migration Plan

1. Créer l'app `apps/changelog/` (`manage.py startapp changelog` dans `apps/`), l'ajouter à `LOCAL_APPS`.
2. Modèle `Version` + migration initiale.
3. `admin.py`, `views.py`, `urls.py`, template `version_list.html`.
4. Inclure les urls dans `config/urls.py`.
5. Ajouter le badge dans `templates/base.html`.
6. Aucune donnée existante à migrer (nouvelle fonctionnalité). Rollback simple : retirer l'app et son inclusion d'urls, supprimer la migration.

## Open Questions

- Faut-il, plus tard, pré-remplir `changements` automatiquement depuis les dossiers `openspec/changes/archive/YYYY-MM-DD-<nom>/proposal.md` créés depuis la dernière version publiée (ex. via une commande `manage.py` d'aide à la création) ? Non résolu — noté comme amélioration future, pas requis pour la V1.
- Faut-il envisager un tag git en parallèle plus tard, une fois le pilier "process de déploiement" formalisé ? À revisiter à ce moment-là, pas maintenant.
