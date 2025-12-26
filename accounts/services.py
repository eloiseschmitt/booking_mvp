"""Service-related helpers for form preparation and persistence."""

from typing import Any

from django.db import transaction
from django.shortcuts import get_object_or_404

from .forms import CategoryForm, ServiceForm
from .models import Service


def prepare_service_form(
    service_id: int | None = None, *, data: dict[str, Any] | None = None
) -> tuple[ServiceForm, Service | None]:
    """Return a service form (optionally bound to an instance) and the service."""
    if service_id:
        service = get_object_or_404(Service, pk=service_id)
        form = (
            ServiceForm(data, instance=service)
            if data is not None
            else ServiceForm(instance=service)
        )
    else:
        service = None
        form = ServiceForm(data) if data is not None else ServiceForm()
    return form, service


def save_service_form(form: ServiceForm, *, user=None):
    """Persist a valid service form and assign the creator when provided."""
    if not form.is_valid():
        return False, form
    with transaction.atomic():
        service = form.save(commit=False)
        if user is not None and service.created_by_id is None:
            service.created_by = user
        service.save()
        form.save_m2m()
    return True, form


def delete_service(service_id: int) -> Service:
    """Delete the given service and return the deleted instance."""
    service = get_object_or_404(Service, pk=service_id)
    service.delete()
    return service


def save_category_form(form: CategoryForm):
    """Persist a valid category form."""
    if not form.is_valid():
        return False, form
    form.save()
    return True, form
