"""Utilitaires de calcul de bornes de periode pour l'analyse de charge ST."""

import calendar
from datetime import date, timedelta


def calculer_bornes_periode(periode: str, date_ref: date | None = None):
    """
    Calcule les bornes d'une periode et de la periode precedente (N-1).

    Args:
        periode: "semaine", "mois", "trimestre", "annee", "custom"
        date_ref: date de reference (defaut: aujourd'hui)

    Returns:
        Tuple (date_du, date_au, date_du_n1, date_au_n1) ou None si custom/inconnu.
    """
    if date_ref is None:
        date_ref = date.today()

    if periode == "semaine":
        lundi = date_ref - timedelta(days=date_ref.weekday())
        dimanche = lundi + timedelta(days=6)
        lundi_n1 = lundi - timedelta(weeks=1)
        dimanche_n1 = lundi - timedelta(days=1)
        return lundi, dimanche, lundi_n1, dimanche_n1

    if periode == "mois":
        du = date_ref.replace(day=1)
        dernier_jour = calendar.monthrange(date_ref.year, date_ref.month)[1]
        au = date_ref.replace(day=dernier_jour)
        # N-1
        if date_ref.month == 1:
            du_n1 = date(date_ref.year - 1, 12, 1)
            au_n1 = date(date_ref.year - 1, 12, 31)
        else:
            du_n1 = date(date_ref.year, date_ref.month - 1, 1)
            dernier_n1 = calendar.monthrange(date_ref.year, date_ref.month - 1)[1]
            au_n1 = date(date_ref.year, date_ref.month - 1, dernier_n1)
        return du, au, du_n1, au_n1

    if periode == "trimestre":
        trimestre = (date_ref.month - 1) // 3
        mois_debut = trimestre * 3 + 1
        du = date(date_ref.year, mois_debut, 1)
        mois_fin = mois_debut + 2
        au = date(date_ref.year, mois_fin, calendar.monthrange(date_ref.year, mois_fin)[1])
        # N-1
        if trimestre == 0:
            du_n1 = date(date_ref.year - 1, 10, 1)
            au_n1 = date(date_ref.year - 1, 12, 31)
        else:
            mois_debut_n1 = (trimestre - 1) * 3 + 1
            mois_fin_n1 = mois_debut_n1 + 2
            du_n1 = date(date_ref.year, mois_debut_n1, 1)
            au_n1 = date(date_ref.year, mois_fin_n1, calendar.monthrange(date_ref.year, mois_fin_n1)[1])
        return du, au, du_n1, au_n1

    if periode == "annee":
        du = date(date_ref.year, 1, 1)
        au = date(date_ref.year, 12, 31)
        du_n1 = date(date_ref.year - 1, 1, 1)
        au_n1 = date(date_ref.year - 1, 12, 31)
        return du, au, du_n1, au_n1

    return None
