from django.contrib import admin

from .models import Category, Service, Workshop


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "duration_minutes", "created_by")
    list_filter = ("category", "created_by")
    search_fields = ("name", "category__name", "created_by__email")
    readonly_fields = ("created_by",)

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Workshop)
class WorkshopAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "city", "zip_code")
    search_fields = ("name", "address", "city", "zip_code")
    filter_horizontal = ("services", "professionals")
