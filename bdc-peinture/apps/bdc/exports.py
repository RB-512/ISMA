"""
Service d'export Excel des BDC pour la facturation.
"""
from datetime import date

from django.db.models import QuerySet
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font

COLONNES = [
    "N° BDC",
    "Bailleur",
    "Adresse",
    "Ville",
    "Sous-traitant",
    "% ST",
    "Montant HT (€)",
    "Montant ST (€)",
    "Date réalisation",
    "Statut",
]


def generer_export_excel(queryset: QuerySet) -> HttpResponse:
    """
    Génère un fichier Excel (.xlsx) à partir d'un queryset de BDC.

    Returns:
        HttpResponse avec le fichier Excel en téléchargement.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Export facturation"

    # En-têtes
    ws.append(COLONNES)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    # Données
    for bdc in queryset.select_related("bailleur", "sous_traitant"):
        ws.append([
            bdc.numero_bdc,
            str(bdc.bailleur),
            bdc.adresse,
            bdc.ville,
            str(bdc.sous_traitant) if bdc.sous_traitant else "",
            float(bdc.pourcentage_st) if bdc.pourcentage_st else None,
            float(bdc.montant_ht) if bdc.montant_ht else None,
            float(bdc.montant_st) if bdc.montant_st else None,
            bdc.date_realisation.strftime("%d/%m/%Y") if bdc.date_realisation else "",
            bdc.get_statut_display(),
        ])

    # Ajuster la largeur des colonnes
    for col in ws.columns:
        max_length = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max_length + 2, 40)

    # Réponse HTTP
    filename = f"export_facturation_{date.today().isoformat()}.xlsx"
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response
