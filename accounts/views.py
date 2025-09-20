from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import CategoryForm, ServiceForm
from .models import Category, Service

@login_required
def dashboard(request):
    section = request.GET.get("section", "overview")
    show_category_form = request.GET.get("show") == "category-form"
    categories = Category.objects.prefetch_related("services").all()
    category_form = CategoryForm()
    service_form = ServiceForm()
    show_service_form = request.GET.get("show") == "service-form"

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
            if service_form.is_valid():
                service_form.save()
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
