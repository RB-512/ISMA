"""
Tests pour l'app monitoring : middleware, vues, commande cleanup.
"""

from datetime import timedelta

import pytest
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from apps.monitoring.middleware import ErrorTrackingMiddleware
from apps.monitoring.models import ErrorReport


# ─── Middleware ───────────────────────────────────────────────────────────────


@pytest.fixture
def middleware():
    return ErrorTrackingMiddleware(get_response=lambda r: None)


@pytest.fixture
def factory():
    return RequestFactory()


@pytest.mark.django_db
def test_middleware_cree_error_report(middleware, factory):
    """Le middleware crée un ErrorReport sur exception non gérée."""
    request = factory.get("/bdc/12/")
    request.user = type("User", (), {"is_authenticated": False})()

    exception = ValueError("quelque chose s'est mal passé")
    middleware.process_exception(request, exception)

    assert ErrorReport.objects.count() == 1
    report = ErrorReport.objects.first()
    assert report.error_type == "ValueError"
    assert "quelque chose s'est mal passé" in report.message
    assert report.count == 1


@pytest.mark.django_db
def test_middleware_incremente_count_sur_doublon(middleware, factory):
    """Le middleware incrémente count si la même erreur se reproduit."""
    request = factory.get("/bdc/12/")
    request.user = type("User", (), {"is_authenticated": False})()

    exception = ValueError("erreur répétée")
    middleware.process_exception(request, exception)
    middleware.process_exception(request, exception)

    assert ErrorReport.objects.count() == 1
    report = ErrorReport.objects.first()
    assert report.count == 2


@pytest.mark.django_db
def test_middleware_ne_plante_pas_si_sauvegarde_echoue(middleware, factory, monkeypatch):
    """Le middleware ne lève pas d'exception si la sauvegarde échoue."""
    request = factory.get("/")
    request.user = type("User", (), {"is_authenticated": False})()

    def raise_error(*args, **kwargs):
        raise RuntimeError("DB down")

    monkeypatch.setattr("apps.monitoring.models.ErrorReport.objects.get_or_create", raise_error)

    exception = KeyError("clé manquante")
    result = middleware.process_exception(request, exception)
    assert result is None  # Ne doit pas propager l'erreur


# ─── Vues ─────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_error_list_accessible_cdt(client_cdt):
    """La vue liste est accessible au CDT."""
    url = reverse("monitoring:error_list")
    response = client_cdt.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_error_list_redirige_secretaire(client_secretaire):
    """La vue liste redirige (403) la Secrétaire."""
    url = reverse("monitoring:error_list")
    response = client_secretaire.get(url)
    assert response.status_code == 403


# ─── Commande cleanup ─────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_cleanup_errors_supprime_entrees_anciennes():
    """La commande supprime les ErrorReport avec last_seen > 30 jours."""
    from django.core.management import call_command

    vieux = ErrorReport.objects.create(
        fingerprint="abc123",
        error_type="OldError",
        message="vieille erreur",
        traceback="...",
        last_seen=timezone.now() - timedelta(days=31),
    )
    recent = ErrorReport.objects.create(
        fingerprint="def456",
        error_type="RecentError",
        message="erreur récente",
        traceback="...",
        last_seen=timezone.now() - timedelta(days=5),
    )

    call_command("cleanup_errors")

    assert not ErrorReport.objects.filter(pk=vieux.pk).exists()
    assert ErrorReport.objects.filter(pk=recent.pk).exists()
