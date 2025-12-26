"""Services for assembling dashboard data."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from django.utils import timezone

from .forms import CategoryForm, ClientForm, ServiceForm
from .models import Category, Service
from .planning import PLANNER_HOURS, build_calendar_events
from .services import prepare_service_form
from .utils import ensure_user_calendar

User = get_user_model()


def _safe_int(value: str | None) -> int | None:
    """Return an int for the provided string, or None when invalid."""
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def initialize_dashboard_state(request) -> dict:
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


def build_dashboard_context(user, state, week_offset: int) -> dict:
    """Aggregate all data needed to render the dashboard."""
    calendar = state.get("calendar")
    clients: list[dict[str, str]] = []
    client_options: list[dict[str, str]] = []
    user_services = []
    is_professional = (
        user.is_authenticated and user.user_type == User.UserType.PROFESSIONAL
    )

    if user.is_authenticated:
        if calendar is None:
            calendar = ensure_user_calendar(user)
            state["calendar"] = calendar
        user_service_qs = Service.objects.filter(created_by=user).order_by("name")
        categories = (
            Category.objects.filter(services__created_by=user)
            .prefetch_related(Prefetch("services", queryset=user_service_qs))
            .distinct()
        )
        user_services = list(user_service_qs)
        if is_professional:
            client_queryset = User.objects.filter(
                user_type=User.UserType.INDIVIDUAL,
                linked_professional=user,
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

    today = timezone.localdate()
    start_of_week = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    end_of_week = start_of_week + timedelta(days=6)
    planner_week_summary = (
        f"Semaine {start_of_week.isocalendar().week} · "
        f"{start_of_week.strftime('%d/%m')} → {end_of_week.strftime('%d/%m')}"
    )

    planning_days = build_calendar_events(calendar, week_offset=week_offset)

    return {
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
