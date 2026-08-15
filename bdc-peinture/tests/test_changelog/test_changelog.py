"""
Tests pour l'app changelog : modèle Version, vue liste, badge sidebar.
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.urls import reverse

from apps.changelog.models import Version

# ─── Modèle ────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_numero_unique(utilisateur_cdt):
    """Deux versions ne peuvent pas partager le même numéro."""
    Version.objects.create(
        numero="2026.08.15",
        date_mise_en_ligne="2026-08-15",
        resume="Première publication",
        created_by=utilisateur_cdt,
    )
    with pytest.raises(IntegrityError):
        Version.objects.create(
            numero="2026.08.15",
            date_mise_en_ligne="2026-08-15",
            resume="Doublon",
            created_by=utilisateur_cdt,
        )


@pytest.mark.django_db
@pytest.mark.parametrize("numero", ["2026.08.15", "2026.08.15-2"])
def test_numero_format_calver_valide(utilisateur_cdt, numero):
    """Les formats AAAA.MM.JJ et AAAA.MM.JJ-N sont acceptés."""
    version = Version(
        numero=numero,
        date_mise_en_ligne="2026-08-15",
        resume="Test",
        created_by=utilisateur_cdt,
    )
    version.full_clean()  # ne doit pas lever


@pytest.mark.django_db
@pytest.mark.parametrize("numero", ["1.4.0", "2026-08-15", "2026.8.15", "abc"])
def test_numero_format_invalide_rejete(utilisateur_cdt, numero):
    """Un numéro qui ne suit pas le format CalVer est rejeté."""
    version = Version(
        numero=numero,
        date_mise_en_ligne="2026-08-15",
        resume="Test",
        created_by=utilisateur_cdt,
    )
    with pytest.raises(ValidationError):
        version.full_clean()


# ─── Vue version_list ────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_version_list_accessible_cdt(client_cdt):
    """La page /nouveautes/ est accessible au CDT."""
    response = client_cdt.get(reverse("changelog:version_list"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_version_list_accessible_secretaire(client_secretaire):
    """La page /nouveautes/ est aussi accessible à la Secrétaire (contrairement à /erreurs/)."""
    response = client_secretaire.get(reverse("changelog:version_list"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_version_list_redirige_anonyme(client):
    """Un utilisateur non authentifié est redirigé vers la page de connexion."""
    response = client.get(reverse("changelog:version_list"))
    assert response.status_code == 302
    assert "/accounts/login/" in response.url


@pytest.mark.django_db
def test_version_list_trie_par_date_decroissante(client_cdt, utilisateur_cdt):
    """Les versions sont affichées de la plus récente à la plus ancienne."""
    Version.objects.create(
        numero="2026.08.01", date_mise_en_ligne="2026-08-01", resume="Ancienne", created_by=utilisateur_cdt
    )
    Version.objects.create(
        numero="2026.08.15", date_mise_en_ligne="2026-08-15", resume="Récente", created_by=utilisateur_cdt
    )

    response = client_cdt.get(reverse("changelog:version_list"))
    versions = list(response.context["page_obj"].object_list)
    assert versions[0].numero == "2026.08.15"
    assert versions[1].numero == "2026.08.01"


# ─── Badge sidebar ───────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_badge_absent_sans_version(client_cdt):
    """Aucun badge n'est affiché tant qu'aucune version n'existe."""
    response = client_cdt.get(reverse("bdc:index"))
    assert (
        "changelog:version_list" not in response.content.decode()
        or reverse("changelog:version_list") not in response.content.decode()
    )


@pytest.mark.django_db
def test_badge_affiche_derniere_version(client_cdt, utilisateur_cdt):
    """Le badge affiche le numéro de la version la plus récente et pointe vers /nouveautes/."""
    Version.objects.create(
        numero="2026.08.01", date_mise_en_ligne="2026-08-01", resume="Ancienne", created_by=utilisateur_cdt
    )
    Version.objects.create(
        numero="2026.08.15", date_mise_en_ligne="2026-08-15", resume="Récente", created_by=utilisateur_cdt
    )

    response = client_cdt.get(reverse("bdc:index"))
    content = response.content.decode()
    assert "2026.08.15" in content
    assert reverse("changelog:version_list") in content
