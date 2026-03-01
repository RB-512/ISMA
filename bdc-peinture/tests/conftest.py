"""
Fixtures pytest partagées entre tous les tests.
"""
import pytest
from django.contrib.auth.models import Group, User

from apps.bdc.models import Bailleur, BonDeCommande, StatutChoices
from apps.sous_traitants.models import SousTraitant

# ─── Utilisateurs ────────────────────────────────────────────────────────────

@pytest.fixture
def groupe_secretaire(db) -> Group:
    group, _ = Group.objects.get_or_create(name="Secretaire")
    return group


@pytest.fixture
def groupe_cdt(db) -> Group:
    group, _ = Group.objects.get_or_create(name="CDT")
    return group


@pytest.fixture
def utilisateur_secretaire(db, groupe_secretaire) -> User:
    user = User.objects.create_user(
        username="secretaire_test",
        email="secretaire@test.fr",
        password="testpass123",
        first_name="Sophie",
        last_name="Martin",
    )
    user.groups.add(groupe_secretaire)
    return user


@pytest.fixture
def utilisateur_cdt(db, groupe_cdt) -> User:
    user = User.objects.create_user(
        username="cdt_test",
        email="cdt@test.fr",
        password="testpass123",
        first_name="Pierre",
        last_name="Dupont",
    )
    user.groups.add(groupe_cdt)
    return user


# ─── Bailleurs ────────────────────────────────────────────────────────────────

@pytest.fixture
def bailleur_gdh(db) -> Bailleur:
    return Bailleur.objects.create(nom="Grand Delta Habitat", code="GDH")


@pytest.fixture
def bailleur_erilia(db) -> Bailleur:
    return Bailleur.objects.create(nom="ERILIA", code="ERILIA")


# ─── Sous-traitant ────────────────────────────────────────────────────────────

@pytest.fixture
def sous_traitant(db) -> SousTraitant:
    return SousTraitant.objects.create(
        nom="Dupont Peinture",
        telephone="0612345678",
        email="dupont@peinture.fr",
    )


# ─── BDC ─────────────────────────────────────────────────────────────────────

@pytest.fixture
def bdc_a_traiter(db, bailleur_gdh, utilisateur_secretaire) -> BonDeCommande:
    """BDC minimal en statut A_TRAITER."""
    return BonDeCommande.objects.create(
        numero_bdc="450056",
        bailleur=bailleur_gdh,
        adresse="3 Rue François 1er",
        code_postal="84000",
        ville="Avignon",
        objet_travaux="Reprise peinture SDB suite travaux faïence",
        cree_par=utilisateur_secretaire,
        statut=StatutChoices.A_TRAITER,
    )


@pytest.fixture
def bdc_a_faire(db, bailleur_gdh, utilisateur_secretaire) -> BonDeCommande:
    """BDC complet en statut A_FAIRE (occupation + type_acces + modalite_acces renseignés)."""
    return BonDeCommande.objects.create(
        numero_bdc="450057",
        bailleur=bailleur_gdh,
        adresse="5 Rue de la Paix",
        code_postal="84000",
        ville="Avignon",
        objet_travaux="Peinture complète T3",
        occupation="OCCUPE",
        type_acces="BADGE_CODE",
        modalite_acces="Badge gardien",
        cree_par=utilisateur_secretaire,
        statut=StatutChoices.A_FAIRE,
    )
