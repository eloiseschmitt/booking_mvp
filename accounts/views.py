"""Views for the accounts application."""

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .dashboard_services import build_dashboard_context, initialize_dashboard_state
from .forms import CategoryForm, ClientForm, EventForm, ServiceForm
from .models import Category, Workshop
from .services import (
    delete_service,
    prepare_service_form,
    save_category_form,
    save_service_form,
)
from .client_services import create_client, update_client, delete_client as service_delete_client
from .event_services import create_event, delete_event
from .utils import ensure_user_calendar


def _safe_int(value: str | None) -> int | None:
    """Return an int for the provided string, or None when invalid."""
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _handle_add_category(request, state):
    """Process category creation and toggle modal visibility."""
    state["section"] = "services"
    state["show_category_form"] = True
    form = CategoryForm(request.POST)
    success, form = save_category_form(form)
    state["category_form"] = form
    if success:
        return redirect(f"{reverse('dashboard')}?section=services")
    return None


def _handle_add_service(request, state):
    """Persist a new service and reopen the modal when invalid."""
    state["section"] = "services"
    state["show_service_form"] = True
    form = ServiceForm(request.POST)
    success, form = save_service_form(form, user=request.user)
    state["service_form"] = form
    if success:
        return redirect(f"{reverse('dashboard')}?section=services")
    return None


def _handle_update_service(request, state):
    """Update an existing service with submitted data."""
    state["section"] = "services"
    state["show_service_form"] = True
    service_id = _safe_int(request.POST.get("service_id"))
    form, _ = prepare_service_form(service_id, data=request.POST)
    success, form = save_service_form(form)
    state["service_form"] = form
    if success:
        return redirect(f"{reverse('dashboard')}?section=services")
    return None


def _handle_delete_service(request, state):
    """Remove a service and refresh the services section."""
    state["section"] = "services"
    service_id = _safe_int(request.POST.get("service_id"))
    if service_id:
        delete_service(service_id)
    return redirect(f"{reverse('dashboard')}?section=services")


def _handle_add_client(request, state):
    """Create a new client for the professional, enforcing permissions."""
    state["section"] = "clients"
    state["show_client_modal"] = True
    success, result = create_client(request.user, request.POST)
    if success:
        return redirect(f"{reverse('dashboard')}?section=clients")
    # result is a bound form with errors
    state["client_form"] = result if result is not None else ClientForm(request.POST)
    return None


def _handle_update_client(request, state):
    """Update an existing client linked to the professional."""
    state["section"] = "clients"
    client_id = _safe_int(request.POST.get("client_id"))
    if not client_id:
        messages.error(request, "Client introuvable.")
        return None
    success, result = update_client(request.user, client_id, request.POST)
    state["show_client_modal"] = True
    if success:
        return redirect(f"{reverse('dashboard')}?section=clients")
    # result may be None (not found/authorized) or a bound form with errors
    if result is None:
        messages.error(request, "Client introuvable ou non autorisé.")
        return None
    state["client_form"] = result
    return None


def _handle_delete_client(request, state):
    """Delete a client linked to the professional."""
    state["section"] = "clients"
    client_id = _safe_int(request.POST.get("client_id"))
    if not client_id:
        messages.error(request, "Client introuvable.")
        return None
    success, message = service_delete_client(request.user, client_id)
    if not success:
        messages.error(request, message or "Client introuvable ou non autorisé.")
        return None
    messages.success(request, "Le client a été supprimé.")
    return redirect(f"{reverse('dashboard')}?section=clients")


def _handle_add_event(request, state):
    """Create a calendar event from the planning modal."""
    state["section"] = "planning"
    if not request.user.is_authenticated:
        return redirect("login")
    if not request.user.is_professional:
        messages.error(
            request,
            "Vous devez être un professionnel pour planifier un rendez-vous.",
        )
        return None

    calendar = ensure_user_calendar(request.user)
    state["calendar"] = calendar
    form = EventForm(request.POST)
    if not form.is_valid():
        messages.error(
            request,
            "Veuillez sélectionner un horaire, une prestation et un client.",
        )
        return None

    success, result = create_event(
        request.user,
        calendar,
        form.cleaned_data["start_at"],
        form.cleaned_data["end_at"],
        form.cleaned_data["service_id"],
        form.cleaned_data["client_id"],
    )
    if success:
        return redirect(f"{reverse('dashboard')}?section=planning")

    messages.error(request, result or "Impossible de créer le rendez-vous. Vérifiez les informations fournies.")
    return None


def _handle_delete_event(request, state):
    """Delete an existing event owned by the professional."""
    state["section"] = "planning"
    if not request.user.is_authenticated:
        return redirect("login")
    if not request.user.is_professional:
        messages.error(
            request, "Vous devez être un professionnel pour gérer vos rendez-vous."
        )
        return None

    event_id = _safe_int(request.POST.get("event_id"))
    if not event_id:
        messages.error(request, "Rendez-vous introuvable.")
        return None

    success, message = delete_event(request.user, event_id)
    if not success:
        messages.error(
            request,
            message or "Vous ne pouvez supprimer que les rendez-vous appartenant à votre agenda.",
        )
        return None

    messages.success(request, "Le rendez-vous a été supprimé.")
    return redirect(f"{reverse('dashboard')}?section=planning")


def _dispatch_dashboard_action(request, state) -> HttpResponse | None:
    """Invoke the handler that matches the submitted dashboard action."""
    action = request.POST.get("action")
    handler = DASHBOARD_ACTION_HANDLERS.get(action)
    if handler:
        return handler(request, state)
    return None


DASHBOARD_ACTION_HANDLERS = {
    "add_category": _handle_add_category,
    "add_service": _handle_add_service,
    "update_service": _handle_update_service,
    "delete_service": _handle_delete_service,
    "add_client": _handle_add_client,
    "update_client": _handle_update_client,
    "delete_client": _handle_delete_client,
    "add_event": _handle_add_event,
    "delete_event": _handle_delete_event,
}


@login_required
def dashboard(request):
    """Render the dashboard and handle service/category management."""
    state = initialize_dashboard_state(request)
    if request.method == "POST":
        response = _dispatch_dashboard_action(request, state)
        if response:
            return response
    week_offset = _safe_int(request.GET.get("week_offset"))
    if week_offset is None:
        week_offset = 0
    context = build_dashboard_context(request.user, state, week_offset)
    return render(request, "accounts/dashboard.html", context)


@login_required
def logout_view(request):
    """Log the user out via POST and redirect otherwise."""
    if request.method == "POST":
        logout(request)
        return redirect("login")
    return redirect("dashboard")


def workshop_detail(request, pk):
    """Display workshop details grouped by service category."""
    workshop = get_object_or_404(
        Workshop.objects.prefetch_related("services__category"), pk=pk
    )
    services_by_category = {}
    for service in workshop.services.all():
        services_by_category.setdefault(service.category, []).append(service)

    context = {
        "workshop": workshop,
        "services_by_category": services_by_category,
        "workshop_photo": workshop.photo or "img/elio-santos-5ZQn_gWKvLE-unsplash.jpg",
    }
    return render(request, "accounts/workshop_detail.html", context)
