"""
Tests — fusion de deux fiches sous-traitant créées pour le même artisan.

Enjeu : tant que le doublon existe, la charge d'un sous-traitant est scindée entre
deux identités et le conducteur de travaux ne voit que la moitié de ses bons.
"""

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.bdc.models import BonDeCommande, ReleveFacturation, StatutChoices
from apps.sous_traitants.models import SousTraitant
from apps.sous_traitants.services import (
    FusionError,
    detecter_doublons,
    fusionner_sous_traitants,
    nom_normalise,
)


@pytest.fixture
def st_garde(db):
    return SousTraitant.objects.create(nom="Dupont Peinture", telephone="0611111111")


@pytest.fixture
def st_doublon(db):
    return SousTraitant.objects.create(nom="DUPONT  Peinture", telephone="0622222222")


def _creer_bdc(numero, bailleur, user, st, statut=StatutChoices.EN_COURS):
    return BonDeCommande.objects.create(
        numero_bdc=numero,
        bailleur=bailleur,
        adresse="1 rue des Tests",
        cree_par=user,
        sous_traitant=st,
        statut=statut,
        montant_st=Decimal("500.00"),
    )


# ─── Normalisation et détection ───────────────────────────────────────────────


class TestNomNormalise:
    @pytest.mark.parametrize(
        "brut",
        ["Dupont Peinture", "DUPONT  PEINTURE", "  dupont peinture  ", "Dupont-Peinture", "Dûpont Péinture"],
    )
    def test_variantes_donnent_le_meme_nom(self, brut):
        assert nom_normalise(brut) == "dupont peinture"

    def test_noms_differents_ne_collisionnent_pas(self):
        assert nom_normalise("Dupont Peinture") != nom_normalise("Martin Peinture")


class TestDetecterDoublons:
    def test_detecte_variante_orthographique(self, st_garde, st_doublon):
        groupes = detecter_doublons()

        assert len(groupes) == 1
        assert {st.pk for st in groupes[0]} == {st_garde.pk, st_doublon.pk}

    def test_aucun_doublon_si_noms_distincts(self, st_garde, db):
        SousTraitant.objects.create(nom="Martin Peinture", telephone="0633333333")

        assert detecter_doublons() == []


# ─── Fusion ───────────────────────────────────────────────────────────────────


class TestFusionnerSousTraitants:
    def test_bdc_reaffectes(self, st_garde, st_doublon, bailleur_gdh, utilisateur_secretaire):
        _creer_bdc("900001", bailleur_gdh, utilisateur_secretaire, st_garde)
        _creer_bdc("900002", bailleur_gdh, utilisateur_secretaire, st_doublon)
        _creer_bdc("900003", bailleur_gdh, utilisateur_secretaire, st_doublon)

        resultat = fusionner_sous_traitants(st_garde, st_doublon)

        assert resultat["bdc"] == 2
        assert BonDeCommande.objects.filter(sous_traitant=st_garde).count() == 3
        assert BonDeCommande.objects.filter(sous_traitant=st_doublon).count() == 0

    def test_aucun_bdc_orphelin(self, st_garde, st_doublon, bailleur_gdh, utilisateur_secretaire):
        """BonDeCommande.sous_traitant est en SET_NULL : le risque est réel."""
        _creer_bdc("900004", bailleur_gdh, utilisateur_secretaire, st_doublon)

        fusionner_sous_traitants(st_garde, st_doublon)

        assert not BonDeCommande.objects.filter(sous_traitant__isnull=True).exists()

    def test_doublon_desactive_mais_conserve(self, st_garde, st_doublon):
        fusionner_sous_traitants(st_garde, st_doublon)

        st_doublon.refresh_from_db()
        assert st_doublon.actif is False
        assert SousTraitant.objects.filter(pk=st_doublon.pk).exists()

    def test_releves_reaffectes_et_renumerotes(self, st_garde, st_doublon, utilisateur_cdt):
        """unique_together (sous_traitant, numero) : un update() brut collisionnerait."""
        ReleveFacturation.objects.create(numero=1, sous_traitant=st_garde, cree_par=utilisateur_cdt)
        ReleveFacturation.objects.create(numero=1, sous_traitant=st_doublon, cree_par=utilisateur_cdt)
        ReleveFacturation.objects.create(numero=2, sous_traitant=st_doublon, cree_par=utilisateur_cdt)

        resultat = fusionner_sous_traitants(st_garde, st_doublon)

        assert resultat["releves"] == 2
        numeros = sorted(ReleveFacturation.objects.filter(sous_traitant=st_garde).values_list("numero", flat=True))
        assert numeros == [1, 2, 3]
        assert ReleveFacturation.objects.filter(sous_traitant=st_doublon).count() == 0

    def test_doublon_supprimable_apres_fusion(self, st_garde, st_doublon, bailleur_gdh, utilisateur_secretaire):
        """Tout l'intérêt de réaffecter d'abord : PROTECT n'a plus rien à retenir."""
        _creer_bdc("900005", bailleur_gdh, utilisateur_secretaire, st_doublon)

        fusionner_sous_traitants(st_garde, st_doublon)
        st_doublon.delete()

        assert not SousTraitant.objects.filter(nom="DUPONT  Peinture").exists()
        assert BonDeCommande.objects.get(numero_bdc="900005").sous_traitant == st_garde

    def test_fusion_avec_soi_meme_refusee(self, st_garde):
        with pytest.raises(FusionError, match="lui-même"):
            fusionner_sous_traitants(st_garde, st_garde)


# ─── Vue et permissions ───────────────────────────────────────────────────────


class TestVueFusion:
    def test_cdt_accede_a_la_page(self, client_cdt, st_garde, st_doublon):
        response = client_cdt.get(reverse("sous_traitants:fusionner"))

        assert response.status_code == 200

    def test_secretaire_refusee(self, client_secretaire):
        response = client_secretaire.get(reverse("sous_traitants:fusionner"))

        assert response.status_code == 403

    def test_post_fusionne(self, client_cdt, st_garde, st_doublon, bailleur_gdh, utilisateur_secretaire):
        _creer_bdc("900006", bailleur_gdh, utilisateur_secretaire, st_doublon)

        response = client_cdt.post(
            reverse("sous_traitants:fusionner"),
            {"garde": st_garde.pk, "doublon": st_doublon.pk},
        )

        assert response.status_code == 200
        assert BonDeCommande.objects.get(numero_bdc="900006").sous_traitant == st_garde
        st_doublon.refresh_from_db()
        assert st_doublon.actif is False
