from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import CategoryForm, ServiceForm
from .models import Category, Service, Workshop
from .services import delete_service, prepare_service_form, save_service_form

@login_required
def dashboard(request):
    section = request.GET.get("section", "overview")
    show_category_form = request.GET.get("show") == "category-form"
    categories = Category.objects.prefetch_related("services").all()
    category_form = CategoryForm()
    service_form = ServiceForm()
    show_service_form = request.GET.get("show") == "service-form"
    service_id_param = request.GET.get("service_id")

    if service_id_param:
        service_form, _ = prepare_service_form(service_id_param)
        show_service_form = True
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
            else:
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

    context = {
        "section": section,
        "categories": categories,
        "category_form": category_form,
        "show_category_form": show_category_form,
        "service_form": service_form,
        "show_service_form": show_service_form,
    }
    return render(request, "accounts/dashboard.html", context)


@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("login")
    return redirect("dashboard")


def workshop_detail(request, pk):
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
