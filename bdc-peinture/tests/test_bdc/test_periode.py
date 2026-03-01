"""Tests unitaires du calcul de bornes de periode."""

from datetime import date

from apps.bdc.periode import calculer_bornes_periode


class TestCalculerBornesPeriode:
    """Tests de calculer_bornes_periode()."""

    def test_mois_courant(self):
        du, au, du_n1, au_n1 = calculer_bornes_periode("mois", date(2026, 3, 15))
        assert du == date(2026, 3, 1)
        assert au == date(2026, 3, 31)
        assert du_n1 == date(2026, 2, 1)
        assert au_n1 == date(2026, 2, 28)

    def test_semaine(self):
        # 2026-03-04 est un mercredi -> semaine lundi 2 -> dimanche 8
        du, au, du_n1, au_n1 = calculer_bornes_periode("semaine", date(2026, 3, 4))
        assert du == date(2026, 3, 2)  # lundi
        assert au == date(2026, 3, 8)  # dimanche
        assert du_n1 == date(2026, 2, 23)
        assert au_n1 == date(2026, 3, 1)

    def test_trimestre(self):
        du, au, du_n1, au_n1 = calculer_bornes_periode("trimestre", date(2026, 5, 10))
        assert du == date(2026, 4, 1)  # T2
        assert au == date(2026, 6, 30)
        assert du_n1 == date(2026, 1, 1)  # T1
        assert au_n1 == date(2026, 3, 31)

    def test_annee(self):
        du, au, du_n1, au_n1 = calculer_bornes_periode("annee", date(2026, 7, 1))
        assert du == date(2026, 1, 1)
        assert au == date(2026, 12, 31)
        assert du_n1 == date(2025, 1, 1)
        assert au_n1 == date(2025, 12, 31)

    def test_custom_retourne_none(self):
        result = calculer_bornes_periode("custom", date(2026, 3, 1))
        assert result is None

    def test_sans_date_ref_utilise_aujourdhui(self):
        du, au, _, _ = calculer_bornes_periode("mois")
        assert du.day == 1
        assert du.month == date.today().month

    def test_periode_inconnue_retourne_none(self):
        result = calculer_bornes_periode("biannuel", date(2026, 1, 1))
        assert result is None

    def test_mois_janvier_n1_decembre(self):
        du, au, du_n1, au_n1 = calculer_bornes_periode("mois", date(2026, 1, 15))
        assert du == date(2026, 1, 1)
        assert au == date(2026, 1, 31)
        assert du_n1 == date(2025, 12, 1)
        assert au_n1 == date(2025, 12, 31)

    def test_trimestre_t1_n1_est_t4_annee_prec(self):
        du, au, du_n1, au_n1 = calculer_bornes_periode("trimestre", date(2026, 2, 1))
        assert du == date(2026, 1, 1)
        assert au == date(2026, 3, 31)
        assert du_n1 == date(2025, 10, 1)
        assert au_n1 == date(2025, 12, 31)
