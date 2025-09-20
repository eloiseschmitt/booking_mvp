from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import CategoryForm
from .models import Category

@login_required
def dashboard(request):
    section = request.GET.get("section", "overview")
    show_category_form = request.GET.get("show") == "category-form"
    categories = Category.objects.prefetch_related("services").all()
    category_form = CategoryForm()

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
        else:
            section = "overview"

    context = {
        "section": section,
        "categories": categories,
        "category_form": category_form,
        "show_category_form": show_category_form,
    }
    return render(request, "accounts/dashboard.html", context)


@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("login")
    return redirect("dashboard")
