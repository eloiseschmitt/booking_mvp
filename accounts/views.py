"""Views for the accounts application."""

from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string

from .forms import CategoryForm, ClientForm, ServiceForm
from .models import Category, Event, EventAttendee, Service, Workshop
from .planning import PLANNER_HOURS, build_calendar_events
from .services import delete_service, prepare_service_form, save_service_form
from .utils import ensure_user_calendar

User = get_user_model()


def _safe_int(value: str | None) -> int | None:
    """Return an int for the provided string, or None when invalid."""

    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _parse_iso_datetime(value: str | None) -> datetime | None:
    """Parse ISO datetime strings and return aware datetimes."""

    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed, timezone.get_current_timezone())

    # Drop the client-provided offset to keep the local value exactly as entered.
    naive_local = parsed.replace(tzinfo=None)
    return timezone.make_aware(naive_local, timezone.get_current_timezone())
    return parsed


def _initialize_dashboard_state(request):
    """Prepare base state (forms, flags) for the dashboard view."""

    section = request.GET.get("section", "overview")
    show_category_form = request.GET.get("show") == "category-form"
    show_service_form = request.GET.get("show") == "service-form"
    category_form = CategoryForm()
    service_form = ServiceForm()
    client_initial = (
        {"linked_professional": request.user.pk}
        if request.user.is_authenticated
        else None
    )
    client_form = ClientForm(initial=client_initial)

    service_id_param = _safe_int(request.GET.get("service_id"))
    category_for_new_service = request.GET.get("category")

    if service_id_param:
        service_form, _ = prepare_service_form(service_id_param)
        show_service_form = True
        section = "services"
    elif show_service_form and category_for_new_service:
        if Category.objects.filter(pk=category_for_new_service).exists():
            service_form = ServiceForm(initial={"category": category_for_new_service})
            section = "services"

    return {
        "section": section,
        "category_form": category_form,
        "service_form": service_form,
        "client_form": client_form,
        "show_category_form": show_category_form,
        "show_service_form": show_service_form,
        "show_client_modal": False,
        "calendar": None,
    }


def _handle_add_category(request, state):
    """Process category creation and toggle modal visibility."""
    state["section"] = "services"
    state["show_category_form"] = True
    state["category_form"] = CategoryForm(request.POST)
    if state["category_form"].is_valid():
        state["category_form"].save()
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
    client_data = request.POST.copy()
    client_data["linked_professional"] = request.user.pk
    client_form = ClientForm(client_data)
    state["client_form"] = client_form
    if not request.user.is_professional:
        client_form.add_error(
            None, "Vous devez être un professionnel pour ajouter un client."
        )
        return None

    if client_form.is_valid():
        client = client_form.save(commit=False)
        client.user_type = User.UserType.INDIVIDUAL
        client.linked_professional = request.user
        client.set_password(get_random_string(12))
        client.save()
        return redirect(f"{reverse('dashboard')}?section=clients")
    return None


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
    start_at_raw = request.POST.get("start_at")
    end_at_raw = request.POST.get("end_at")
    service_id = request.POST.get("service_id")
    client_id = request.POST.get("client_id")
    if not (start_at_raw and end_at_raw and service_id and client_id):
        messages.error(
            request,
            "Veuillez sélectionner un horaire, une prestation et un client.",
        )
        return None

    event_created = _create_event_from_form(
        request.user, calendar, start_at_raw, end_at_raw, service_id, client_id
    )
    if event_created:
        return redirect(f"{reverse('dashboard')}?section=planning")

    messages.error(
        request,
        "Impossible de créer le rendez-vous. Vérifiez les informations fournies.",
    )
    return None


def _dispatch_dashboard_action(request, state) -> HttpResponse | None:
    """Invoke the handler that matches the submitted dashboard action."""
    action = request.POST.get("action")
    handler = DASHBOARD_ACTION_HANDLERS.get(action)
    if handler:
        return handler(request, state)
    return None


def _build_dashboard_context(request, state):
    """Aggregate all data needed to render the dashboard."""

    calendar = state.get("calendar")
    clients: list[dict[str, str]] = []
    client_options: list[dict[str, str]] = []
    user_services = []
    is_professional = (
        request.user.is_authenticated
        and request.user.user_type == User.UserType.PROFESSIONAL
    )

    if request.user.is_authenticated:
        if calendar is None:
            calendar = ensure_user_calendar(request.user)
            state["calendar"] = calendar
        user_service_qs = Service.objects.filter(created_by=request.user).order_by(
            "name"
        )
        categories = (
            Category.objects.filter(services__created_by=request.user)
            .prefetch_related(Prefetch("services", queryset=user_service_qs))
            .distinct()
        )
        user_services = list(user_service_qs)
        if is_professional:
            client_queryset = User.objects.filter(
                user_type=User.UserType.INDIVIDUAL,
                linked_professional=request.user,
            ).order_by("first_name", "last_name", "email")
            for client in client_queryset:
                full_name = (
                    f"{client.first_name} {client.last_name}".strip()
                ) or client.email
                client_data = {
                    "id": client.pk,
                    "full_name": full_name,
                    "email": client.email,
                    "phone": getattr(client, "phone_number", "") or "—",
                }
                clients.append(client_data)
                client_options.append(
                    {
                        "id": client.pk,
                        "label": full_name,
                    }
                )
    else:
        categories = Category.objects.none()

    try:
        week_offset = int(request.GET.get("week_offset", "0"))
    except (TypeError, ValueError):
        week_offset = 0

    today = timezone.localdate()
    start_of_week = (
        today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    )
    end_of_week = start_of_week + timedelta(days=6)
    planner_week_summary = (
        f"Semaine {start_of_week.isocalendar().week} · "
        f"{start_of_week.strftime('%d/%m')} → {end_of_week.strftime('%d/%m')}"
    )

    planning_days = build_calendar_events(calendar, week_offset=week_offset)

    context = {
        "section": state["section"],
        "categories": categories,
        "category_form": state["category_form"],
        "show_category_form": state["show_category_form"],
        "show_category_modal": state["show_category_form"]
        or bool(state["category_form"].errors),
        "service_form": state["service_form"],
        "show_service_form": state["show_service_form"],
        "show_service_modal": state["show_service_form"]
        or bool(state["service_form"].errors),
        "client_form": state["client_form"],
        "show_client_modal": state["show_client_modal"]
        or bool(state["client_form"].errors),
        "is_professional": is_professional,
        "planner_hours": PLANNER_HOURS,
        "planning_days": planning_days,
        "week_offset": week_offset,
        "planner_week_summary": planner_week_summary,
        "user_services": user_services,
        "clients": clients,
        "client_options": client_options,
    }
    return context


DASHBOARD_ACTION_HANDLERS = {
    "add_category": _handle_add_category,
    "add_service": _handle_add_service,
    "update_service": _handle_update_service,
    "delete_service": _handle_delete_service,
    "add_client": _handle_add_client,
    "add_event": _handle_add_event,
}


@login_required
def dashboard(request):
    """Render the dashboard and handle service/category management."""
    state = _initialize_dashboard_state(request)
    if request.method == "POST":
        response = _dispatch_dashboard_action(request, state)
        if response:
            return response
    context = _build_dashboard_context(request, state)
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


def _create_event_from_form(
    user, calendar, start_at_raw, end_at_raw, service_id, client_id
):
    """Return True if the event was created successfully."""

    if not calendar:
        return False
    start_at = _parse_iso_datetime(start_at_raw)
    if start_at is None:
        return False
    end_at = _parse_iso_datetime(end_at_raw)
    if end_at is None:
        end_at = start_at

    service = Service.objects.filter(pk=service_id, created_by=user).first()
    client = User.objects.filter(
        pk=client_id,
        linked_professional=user,
        user_type=User.UserType.INDIVIDUAL,
    ).first()
    if not (service and client):
        return False

    if end_at <= start_at:
        duration = service.duration_minutes or 60
        end_at = start_at + timedelta(minutes=duration)
    event = Event.objects.create(
        calendar=calendar,
        title=service.name,
        description=service.description or "",
        start_at=start_at,
        end_at=end_at,
        created_by=user,
        status="planned",
    )
    EventAttendee.objects.create(event=event, user=client)
    return True
