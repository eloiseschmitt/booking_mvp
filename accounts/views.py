"""Views for the accounts application."""

from datetime import timedelta

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import CategoryForm, ServiceForm
from .models import Calendar, Category, Workshop
from .planning import PLANNER_HOURS, build_calendar_events
from .services import delete_service, prepare_service_form, save_service_form


@login_required
def dashboard(request):
    """Render the dashboard and handle service/category management."""
    # pylint: disable=too-many-branches,too-many-statements,too-many-locals
    section = request.GET.get("section", "overview")
    show_category_form = request.GET.get("show") == "category-form"
    categories = Category.objects.prefetch_related("services").all()
    category_form = CategoryForm()
    service_form = ServiceForm()
    show_service_form = request.GET.get("show") == "service-form"
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
        else:
            section = "overview"

    calendar = None
    if request.user.is_authenticated:
        calendar = Calendar.objects.filter(owner=request.user).first()
        if calendar is None:
            calendar = Calendar.objects.filter(is_public=True).first()

    try:
        week_offset = int(request.GET.get("week_offset", "0"))
    except (TypeError, ValueError):
        week_offset = 0

    today = timezone.localdate()
    start_of_week = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
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
        "service_form": service_form,
        "show_service_form": show_service_form,
        "planner_hours": PLANNER_HOURS,
        "planning_days": build_calendar_events(calendar, week_offset=week_offset),
        "week_offset": week_offset,
        "planner_week_summary": planner_week_summary,
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
