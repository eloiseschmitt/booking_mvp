"""URL configuration for the accounts' app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("logout/", views.logout_view, name="logout"),
    path("workshops/<int:pk>/", views.workshop_detail, name="workshop_detail"),
]
