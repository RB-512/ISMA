from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import group_required
from apps.sous_traitants.forms import SousTraitantForm
from apps.sous_traitants.models import SousTraitant
from apps.sous_traitants.services import FusionError, detecter_doublons, fusionner_sous_traitants


@login_required
def liste_sous_traitants(request):
    q = request.GET.get("q", "").strip()
    sous_traitants = SousTraitant.objects.all()
    if q:
        sous_traitants = sous_traitants.filter(Q(nom__icontains=q) | Q(siret__icontains=q) | Q(ville__icontains=q))
    return render(
        request,
        "sous_traitants/list.html",
        {
            "sous_traitants": sous_traitants,
            "form_creer": SousTraitantForm(),
            "q": q,
        },
    )


@login_required
def creer_sous_traitant(request):
    if request.method != "POST":
        return redirect("sous_traitants:list")
    form = SousTraitantForm(request.POST)
    if form.is_valid():
        st = form.save()
        messages.success(request, f"Sous-traitant « {st.nom} » créé.")
        return redirect("sous_traitants:list")
    # Re-render list with form errors
    q = request.GET.get("q", "").strip()
    sous_traitants = SousTraitant.objects.all()
    return render(
        request,
        "sous_traitants/list.html",
        {
            "sous_traitants": sous_traitants,
            "form_creer": form,
            "q": q,
        },
    )


@login_required
def modifier_sous_traitant(request, pk):
    sous_traitant = get_object_or_404(SousTraitant, pk=pk)
    if request.method == "POST":
        form = SousTraitantForm(request.POST, instance=sous_traitant)
        if form.is_valid():
            form.save()
            messages.success(request, f"Sous-traitant « {sous_traitant.nom} » mis à jour.")
            return redirect("sous_traitants:list")
    else:
        form = SousTraitantForm(instance=sous_traitant)
    return render(
        request,
        "sous_traitants/partials/_modifier_sous_traitant.html",
        {"form": form, "sous_traitant": sous_traitant},
    )


@login_required
def desactiver_sous_traitant(request, pk):
    sous_traitant = get_object_or_404(SousTraitant, pk=pk)
    if request.method == "POST":
        sous_traitant.actif = False
        sous_traitant.save()
        messages.success(request, f"Sous-traitant « {sous_traitant.nom} » désactivé.")
    return redirect("sous_traitants:list")


@login_required
def reactiver_sous_traitant(request, pk):
    sous_traitant = get_object_or_404(SousTraitant, pk=pk)
    if request.method == "POST":
        sous_traitant.actif = True
        sous_traitant.save()
        messages.success(request, f"Sous-traitant « {sous_traitant.nom} » réactivé.")
    return redirect("sous_traitants:list")


@group_required("CDT")
def fusionner_sous_traitant(request):
    """
    Fusionne deux fiches sous-traitant en double.

    Après fusion, l'utilisateur choisit lui-même de supprimer le doublon devenu vide
    ou de le conserver inactif.
    """
    if request.method == "POST":
        garde = get_object_or_404(SousTraitant, pk=request.POST.get("garde"))
        doublon = get_object_or_404(SousTraitant, pk=request.POST.get("doublon"))

        try:
            resultat = fusionner_sous_traitants(garde, doublon)
        except FusionError as e:
            messages.error(request, str(e))
            return redirect("sous_traitants:fusionner")

        return render(
            request,
            "sous_traitants/fusion_resultat.html",
            {"garde": garde, "doublon": doublon, "resultat": resultat},
        )

    return render(
        request,
        "sous_traitants/fusion.html",
        {
            "doublons": detecter_doublons(),
            "sous_traitants": SousTraitant.objects.all().order_by("nom"),
        },
    )


@login_required
def supprimer_sous_traitant(request, pk):
    sous_traitant = get_object_or_404(SousTraitant, pk=pk)
    if request.method == "POST":
        nom = sous_traitant.nom
        try:
            sous_traitant.delete()
            messages.success(request, f"Sous-traitant « {nom} » supprimé.")
        except ProtectedError:
            messages.error(
                request,
                f"Impossible de supprimer « {nom} » car il est lié à des bons de commande. Désactivez-le à la place.",
            )
    return redirect("sous_traitants:list")
