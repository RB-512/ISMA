from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from apps.accounts.decorators import group_required

from .models import PrixForfaitaire


@login_required
@group_required("CDT")
def bibliotheque_liste(request):
    """Liste des prix forfaitaires avec recherche et tri."""
    q = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "asc")

    prix = PrixForfaitaire.objects.all()
    if q:
        prix = prix.filter(Q(reference__icontains=q) | Q(designation__icontains=q))
    prix = prix.order_by("-reference" if sort == "desc" else "reference")

    ctx = {"prix_list": prix, "q": q, "sort": sort}

    if request.headers.get("HX-Request"):
        return render(request, "bdc/partials/_bibliotheque_table.html", ctx)
    return render(request, "bdc/bibliotheque.html", ctx)


@login_required
@group_required("CDT")
def bibliotheque_ajouter(request):
    """Ajout d'un prix forfaitaire (HTMX)."""
    if request.method != "POST":
        return HttpResponse(status=405)

    reference = request.POST.get("reference", "").strip()
    designation = request.POST.get("designation", "").strip()
    unite = request.POST.get("unite", "").strip()
    prix_unitaire = request.POST.get("prix_unitaire", "").strip()

    errors = []
    if not reference:
        errors.append("La référence est obligatoire.")
    if not designation:
        errors.append("La désignation est obligatoire.")
    if not unite:
        errors.append("L'unité est obligatoire.")
    if not prix_unitaire:
        errors.append("Le prix unitaire est obligatoire.")
    if reference and PrixForfaitaire.objects.filter(reference=reference).exists():
        errors.append(f"La référence « {reference} » existe déjà.")

    if errors:
        for e in errors:
            messages.error(request, e)
        prix = PrixForfaitaire.objects.all()
        return render(request, "bdc/partials/_bibliotheque_table.html", {"prix_list": prix})

    PrixForfaitaire.objects.create(
        reference=reference,
        designation=designation,
        unite=unite,
        prix_unitaire=prix_unitaire,
    )
    prix = PrixForfaitaire.objects.all()
    return render(request, "bdc/partials/_bibliotheque_table.html", {"prix_list": prix})


@login_required
@group_required("CDT")
def bibliotheque_modifier(request, pk):
    """Modification d'un prix forfaitaire (HTMX)."""
    prix = get_object_or_404(PrixForfaitaire, pk=pk)

    if request.method == "GET":
        return render(request, "bdc/partials/_bibliotheque_row_edit.html", {"prix": prix})

    prix.reference = request.POST.get("reference", prix.reference).strip()
    prix.designation = request.POST.get("designation", prix.designation).strip()
    prix.unite = request.POST.get("unite", prix.unite).strip()
    prix.prix_unitaire = request.POST.get("prix_unitaire", prix.prix_unitaire)
    prix.save()

    prix_list = PrixForfaitaire.objects.all()
    return render(request, "bdc/partials/_bibliotheque_table.html", {"prix_list": prix_list})


@login_required
@group_required("CDT")
def bibliotheque_supprimer(request, pk):
    """Suppression d'un prix forfaitaire (HTMX)."""
    prix = get_object_or_404(PrixForfaitaire, pk=pk)

    if prix.ligneforfaitattribution_set.exists():
        messages.error(request, "Ce prix est utilisé dans des attributions et ne peut pas être supprimé.")
    else:
        prix.delete()

    prix_list = PrixForfaitaire.objects.all()
    return render(request, "bdc/partials/_bibliotheque_table.html", {"prix_list": prix_list})
