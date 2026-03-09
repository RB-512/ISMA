"""
Export PDF et Excel des relevés de facturation sous-traitant.
"""

from datetime import date

import fitz  # PyMuPDF
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font

from .models import ActionChoices, HistoriqueAction, ReleveFacturation


def _dates_attribution(bdc_ids):
    """Retourne un dict {bdc_id: datetime} des dates d'attribution."""
    attributions = {}
    for ha in HistoriqueAction.objects.filter(
        bdc_id__in=bdc_ids,
        action=ActionChoices.ATTRIBUTION,
    ).order_by("bdc_id", "-created_at"):
        if ha.bdc_id not in attributions:
            attributions[ha.bdc_id] = ha.created_at
    return attributions


# ─── Constantes PDF ─────────────────────────────────────────────────────────

_MARGE_G = 50
_MARGE_D = 50
_Y_START = 60
_INTERLIGNE = 16
_SECTION_GAP = 12


def generer_releve_pdf(releve: ReleveFacturation) -> HttpResponse:
    """Génère un PDF du relevé de facturation (pour le ST)."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4
    width = page.rect.width
    y = _Y_START

    st_nom = releve.sous_traitant.nom.upper()
    debut, fin = releve.periode

    # En-tête
    page.insert_text((_MARGE_G, y), "RELEV\u00c9 DE FACTURATION", fontsize=14, fontname="helv", color=(0.1, 0.1, 0.1))
    y += 22
    page.insert_text((_MARGE_G, y), f"N\u00b0 {releve.numero} \u2014 {st_nom}", fontsize=11, fontname="helv")
    y += _INTERLIGNE
    if debut and fin:
        page.insert_text(
            (_MARGE_G, y),
            f"P\u00e9riode : {debut.strftime('%d/%m/%Y')} \u2014 {fin.strftime('%d/%m/%Y')}",
            fontsize=9,
            fontname="helv",
            color=(0.5, 0.5, 0.5),
        )
        y += _INTERLIGNE

    # Ligne séparation
    y += 4
    page.draw_line(fitz.Point(_MARGE_G, y), fitz.Point(width - _MARGE_D, y), color=(0.2, 0.2, 0.2), width=1)
    y += _INTERLIGNE + _SECTION_GAP

    # En-tête tableau
    col_bdc = _MARGE_G
    col_bailleur = _MARGE_G + 65
    col_adresse = _MARGE_G + 115
    col_attrib = width - _MARGE_D - 140
    col_montant = width - _MARGE_D - 70
    header_color = (0.4, 0.4, 0.4)
    page.insert_text((col_bdc, y), "N\u00b0 BDC", fontsize=8, fontname="helv", color=header_color)
    page.insert_text((col_bailleur, y), "Bailleur", fontsize=8, fontname="helv", color=header_color)
    page.insert_text((col_adresse, y), "Adresse", fontsize=8, fontname="helv", color=header_color)
    page.insert_text((col_attrib, y), "Attribution", fontsize=8, fontname="helv", color=header_color)
    page.insert_text((col_montant, y), "Montant ST", fontsize=8, fontname="helv", color=header_color)
    y += 4
    page.draw_line(fitz.Point(_MARGE_G, y), fitz.Point(width - _MARGE_D, y), color=(0.85, 0.85, 0.85), width=0.5)
    y += _INTERLIGNE - 2

    # Lignes BDC
    bdc_list = list(releve.bdc.select_related("bailleur").order_by("date_realisation"))
    attributions = _dates_attribution([b.pk for b in bdc_list])

    for bdc in bdc_list:
        if y > 780:  # nouvelle page si besoin
            page = doc.new_page(width=595, height=842)
            y = _Y_START

        page.insert_text((col_bdc, y), bdc.numero_bdc, fontsize=8, fontname="helv")
        page.insert_text((col_bailleur, y), bdc.bailleur.code, fontsize=8, fontname="helv")
        adresse = bdc.adresse
        if len(adresse) > 35:
            adresse = adresse[:32] + "..."
        page.insert_text((col_adresse, y), adresse, fontsize=8, fontname="helv")
        date_attr = attributions.get(bdc.pk)
        attr_str = date_attr.strftime("%d/%m/%Y") if date_attr else "\u2014"
        page.insert_text((col_attrib, y), attr_str, fontsize=8, fontname="helv")
        montant_str = f"{bdc.montant_st:.2f} \u20ac" if bdc.montant_st else "\u2014"
        page.insert_text((col_montant, y), montant_str, fontsize=8, fontname="helv")
        y += _INTERLIGNE

    # Total
    y += _SECTION_GAP
    page.draw_line(fitz.Point(_MARGE_G, y), fitz.Point(width - _MARGE_D, y), color=(0.2, 0.2, 0.2), width=0.5)
    y += _INTERLIGNE
    total_str = f"TOTAL : {releve.montant_total:.2f} \u20ac"
    page.insert_text((col_montant - 30, y), total_str, fontsize=11, fontname="helv", color=(0.1, 0.1, 0.1))

    pdf_bytes = doc.tobytes()
    doc.close()

    safe_nom = releve.sous_traitant.nom.replace(" ", "_")
    filename = f"releve_{safe_nom}_{releve.numero}.pdf"
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response


# ─── Excel ───────────────────────────────────────────────────────────────────

COLONNES_RELEVE = [
    "N\u00b0 BDC",
    "Bailleur",
    "Adresse",
    "Ville",
    "Montant ST (\u20ac)",
    "Date attribution",
    "Date r\u00e9alisation",
]


def generer_releve_excel(releve: ReleveFacturation) -> HttpResponse:
    """Génère un Excel du relevé de facturation (pour le CDT)."""
    wb = Workbook()
    ws = wb.active
    ws.title = f"Relev\u00e9 {releve.numero}"

    # En-têtes
    ws.append(COLONNES_RELEVE)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    # Données
    bdc_list = list(releve.bdc.select_related("bailleur").order_by("date_realisation"))
    attributions = _dates_attribution([b.pk for b in bdc_list])

    for bdc in bdc_list:
        date_attr = attributions.get(bdc.pk)
        ws.append(
            [
                bdc.numero_bdc,
                bdc.bailleur.code,
                bdc.adresse,
                bdc.ville,
                float(bdc.montant_st) if bdc.montant_st else None,
                date_attr.strftime("%d/%m/%Y") if date_attr else "",
                bdc.date_realisation.strftime("%d/%m/%Y") if bdc.date_realisation else "",
            ]
        )

    # Largeur colonnes
    for col in ws.columns:
        max_length = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max_length + 2, 40)

    safe_nom = releve.sous_traitant.nom.replace(" ", "_")
    filename = f"releve_{safe_nom}_{releve.numero}_{date.today().isoformat()}.xlsx"
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f"attachment; filename={filename}"
    wb.save(response)
    return response
