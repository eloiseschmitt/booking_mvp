from django.db import transaction
from django.shortcuts import get_object_or_404

from .forms import ServiceForm
from .models import Service


def prepare_service_form(service_id=None, *, data=None):
    if service_id:
        service = get_object_or_404(Service, pk=service_id)
        form = ServiceForm(data, instance=service) if data is not None else ServiceForm(instance=service)
    else:
        service = None
        form = ServiceForm(data) if data is not None else ServiceForm()
    return form, service


def save_service_form(form):
    if not form.is_valid():
        return False, form
    with transaction.atomic():
        form.save()
    return True, form


def delete_service(service_id):
    service = get_object_or_404(Service, pk=service_id)
    service.delete()
    return service
