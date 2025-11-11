"""Views for the accounts application."""

from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string

from .forms import CategoryForm, ClientForm, ServiceForm
from .models import Category, Event, EventAttendee, Service, Workshop
from .utils import ensure_user_calendar
from .planning import PLANNER_HOURS, build_calendar_events
from .services import delete_service, prepare_service_form, save_service_form

User = get_user_model()


@login_required
def dashboard(request):
    """Render the dashboard and handle service/category management."""
    # pylint: disable=too-many-branches,too-many-statements,too-many-locals
    section = request.GET.get("section", "overview")
    show_category_form = request.GET.get("show") == "category-form"
    categories = Category.objects.none()
    category_form = CategoryForm()
    service_form = ServiceForm()
    client_initial = (
        {"linked_professional": request.user.pk}
        if request.user.is_authenticated
        else None
    )
    client_form = ClientForm(initial=client_initial)
    show_service_form = request.GET.get("show") == "service-form"
    show_client_modal = False
    service_id_param = request.GET.get("service_id")
    category_for_new_service = request.GET.get("category")

    if service_id_param:
        service_form, _ = prepare_service_form(service_id_param)
        show_service_form = True
        section = "services"
    elif show_service_form and category_for_new_service:
        if Category.objects.filter(pk=category_for_new_service).exists():
            service_form = ServiceForm(initial={"category": category_for_new_service})
            section = "services"

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_category":
            section = "services"
            category_form = CategoryForm(request.POST)
            show_category_form = True
            if category_form.is_valid():
                category_form.save()
                redirect_url = f"{reverse('dashboard')}?section=services"
                return redirect(redirect_url)
        elif action == "add_service":
            section = "services"
            service_form = ServiceForm(request.POST)
            show_service_form = True
            success, service_form = save_service_form(service_form, user=request.user)
            if success:
                redirect_url = f"{reverse('dashboard')}?section=services"
                return redirect(redirect_url)
        elif action == "update_service":
            section = "services"
            service_id = request.POST.get("service_id")
            form, _ = prepare_service_form(service_id, data=request.POST)
            success, form = save_service_form(form)
            if success:
                redirect_url = f"{reverse('dashboard')}?section=services"
                return redirect(redirect_url)
            show_service_form = True
            service_form = form
        elif action == "delete_service":
            section = "services"
            service_id = request.POST.get("service_id")
            if service_id:
                delete_service(service_id)
            redirect_url = f"{reverse('dashboard')}?section=services"
            return redirect(redirect_url)
        elif action == "add_client":
            section = "clients"
            show_client_modal = True
            client_data = request.POST.copy()
            client_data["linked_professional"] = request.user.pk
            client_form = ClientForm(client_data)
            if request.user.is_professional:
                if client_form.is_valid():
                    client = client_form.save(commit=False)
                    client.user_type = User.UserType.INDIVIDUAL
                    client.linked_professional = request.user
                    client.set_password(get_random_string(12))
                    client.save()
                    redirect_url = f"{reverse('dashboard')}?section=clients"
                    return redirect(redirect_url)
            else:
                client_form.add_error(
                    None, "Vous devez être un professionnel pour ajouter un client."
                )
        elif action == "add_event":
            section = "planning"
            if not request.user.is_authenticated:
                return redirect("login")
            if not request.user.is_professional:
                messages.error(
                    request,
                    "Vous devez être un professionnel pour planifier un rendez-vous.",
                )
            else:
                calendar = ensure_user_calendar(request.user)
                start_at_raw = request.POST.get("start_at")
                service_id = request.POST.get("service_id")
                client_id = request.POST.get("client_id")
                if not (start_at_raw and service_id and client_id):
                    messages.error(
                        request,
                        "Veuillez sélectionner un horaire, une prestation et un client.",
                    )
                else:
                    event_created = _create_event_from_form(
                        request.user, calendar, start_at_raw, service_id, client_id
                    )
                    if event_created:
                        return redirect(f"{reverse('dashboard')}?section=planning")
                    messages.error(
                        request,
                        "Impossible de créer le rendez-vous. Vérifiez les informations fournies.",
                    )
    calendar = None
    clients: list[dict[str, str]] = []
    client_options: list[dict[str, str]] = []
    user_services = []
    is_professional = (
        request.user.is_authenticated
        and request.user.user_type == User.UserType.PROFESSIONAL
    )
    if request.user.is_authenticated:
        calendar = ensure_user_calendar(request.user)
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

    context = {
        "section": section,
        "categories": categories,
        "category_form": category_form,
        "show_category_form": show_category_form,
        "show_category_modal": show_category_form or bool(category_form.errors),
        "service_form": service_form,
        "show_service_form": show_service_form,
        "show_service_modal": show_service_form or bool(service_form.errors),
        "client_form": client_form,
        "show_client_modal": show_client_modal or bool(client_form.errors),
        "is_professional": is_professional,
        "planner_hours": PLANNER_HOURS,
        "planning_days": build_calendar_events(calendar, week_offset=week_offset),
        "week_offset": week_offset,
        "planner_week_summary": planner_week_summary,
        "user_services": user_services,
        "clients": clients,
        "client_options": client_options,
    }
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


def _create_event_from_form(user, calendar, start_at_raw, service_id, client_id):
    """Return True if the event was created successfully."""

    if not calendar:
        return False
    try:
        start_at = datetime.fromisoformat(start_at_raw)
    except (TypeError, ValueError):
        return False
    if timezone.is_naive(start_at):
        start_at = timezone.make_aware(start_at, timezone.get_current_timezone())

    service = Service.objects.filter(pk=service_id, created_by=user).first()
    client = User.objects.filter(
        pk=client_id,
        linked_professional=user,
        user_type=User.UserType.INDIVIDUAL,
    ).first()
    if not (service and client):
        return False

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
