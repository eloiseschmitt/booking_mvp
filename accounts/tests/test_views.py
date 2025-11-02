"""Tests for accounts views."""

# pylint: disable=missing-class-docstring,missing-function-docstring,no-member

from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.constants import PLANNER_HOURS
from accounts.models import Category, Service, Workshop

User = get_user_model()


class DashboardViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com",
            password="safe-password",
            user_type=User.UserType.PROFESSIONAL,
        )
        self.url = reverse("dashboard")

    def login(self):
        logged_in = self.client.login(email=self.user.email, password="safe-password")
        self.assertTrue(logged_in)

    def test_dashboard_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)
        self.assertIn("next=", response.url)

    def test_dashboard_get_default_context(self):
        self.login()
        category = Category.objects.create(name="Modelage")
        Service.objects.create(
            category=category,
            name="Massage relaxant",
            created_by=self.user,
            price="55.00",
            duration_minutes=60,
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["section"], "overview")
        self.assertIn(category, list(response.context["categories"]))
        self.assertFalse(response.context["show_category_form"])
        self.assertFalse(response.context["show_service_form"])
        self.assertEqual(response.context["planner_hours"], PLANNER_HOURS)
        planning_days = response.context["planning_days"]
        self.assertIsInstance(planning_days, list)
        self.assertGreaterEqual(len(planning_days), 1)
        first_day = planning_days[0]
        self.assertIn("label", first_day)
        self.assertIn("date", first_day)
        self.assertIn("events", first_day)

    def test_dashboard_get_with_service_id_prefills_form(self):
        self.login()
        mock_form = MagicMock()

        with patch(
            "accounts.views.prepare_service_form", return_value=(mock_form, object())
        ) as mocked_prepare:
            response = self.client.get(self.url, {"service_id": "42"})

        mocked_prepare.assert_called_once_with("42")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["service_form"], mock_form)
        self.assertTrue(response.context["show_service_form"])
        self.assertEqual(response.context["section"], "services")

    def test_dashboard_get_shows_service_form_for_new_service(self):
        self.login()
        category = Category.objects.create(name="Coiffure")

        response = self.client.get(
            self.url, {"show": "service-form", "category": str(category.pk)}
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["show_service_form"])
        self.assertEqual(response.context["section"], "services")
        self.assertEqual(
            response.context["service_form"].initial["category"], str(category.pk)
        )

    def test_dashboard_post_add_category_creates_new_category(self):
        self.login()

        response = self.client.post(
            self.url, {"action": "add_category", "name": "Nouveaux soins"}
        )

        self.assertRedirects(response, f"{self.url}?section=services")
        self.assertTrue(Category.objects.filter(name="Nouveaux soins").exists())

    def test_dashboard_post_add_service_creates_service(self):
        self.login()
        category = Category.objects.create(name="Esthétique")

        response = self.client.post(
            self.url,
            {
                "action": "add_service",
                "name": "Soin visage",
                "category": str(category.pk),
                "price": "65.50",
                "duration_minutes": "75",
            },
        )

        self.assertRedirects(response, f"{self.url}?section=services")
        service = Service.objects.get(name="Soin visage")
        self.assertEqual(service.category, category)
        self.assertEqual(service.created_by, self.user)
        self.assertEqual(service.price, Decimal("65.50"))

    def test_dashboard_post_update_service_updates_existing_service(self):
        self.login()
        category = Category.objects.create(name="Sophrologie")
        service = Service.objects.create(
            category=category,
            name="Séance découverte",
            created_by=self.user,
            price="45.00",
            duration_minutes=45,
        )

        response = self.client.post(
            self.url,
            {
                "action": "update_service",
                "service_id": str(service.pk),
                "name": "Séance approfondie",
                "category": str(category.pk),
                "price": "55.00",
                "duration_minutes": "60",
            },
        )

        self.assertRedirects(response, f"{self.url}?section=services")
        service.refresh_from_db()
        self.assertEqual(service.name, "Séance approfondie")
        self.assertEqual(service.duration_minutes, 60)
        self.assertEqual(str(service.price), "55.00")

    def test_dashboard_post_update_service_invalid_form_shows_errors(self):
        self.login()
        category = Category.objects.create(name="Massages")
        service = Service.objects.create(
            category=category,
            name="Massage pierres chaudes",
            created_by=self.user,
            price="80.00",
            duration_minutes=90,
        )

        response = self.client.post(
            self.url,
            {
                "action": "update_service",
                "service_id": str(service.pk),
                "name": " ",
                "category": str(category.pk),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["show_service_form"])
        form = response.context["service_form"]
        self.assertIn("name", form.errors)
        service.refresh_from_db()
        self.assertEqual(service.name, "Massage pierres chaudes")

    def test_dashboard_post_delete_service_removes_service(self):
        self.login()
        category = Category.objects.create(name="Bien-être")
        service = Service.objects.create(
            category=category,
            name="Yoga express",
            created_by=self.user,
            price="30.00",
            duration_minutes=30,
        )

        response = self.client.post(
            self.url, {"action": "delete_service", "service_id": str(service.pk)}
        )

        self.assertRedirects(response, f"{self.url}?section=services")
        self.assertFalse(Service.objects.filter(pk=service.pk).exists())


class LogoutViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="member@example.com",
            password="safe-password",
        )
        self.url = "/logout/"

    def login(self):
        logged_in = self.client.login(email=self.user.email, password="safe-password")
        self.assertTrue(logged_in)

    def test_logout_via_post_logs_user_out(self):
        self.login()

        with patch("accounts.views.logout") as mocked_logout:
            response = self.client.post(self.url)

        mocked_logout.assert_called_once()
        self.assertRedirects(response, reverse("login"))

    def test_logout_via_get_redirects_dashboard(self):
        self.login()

        response = self.client.get(self.url)

        self.assertRedirects(response, reverse("dashboard"))


class WorkshopDetailViewTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Ateliers créatifs")
        self.user = User.objects.create_user(
            email="creator@example.com",
            password="safe-password",
        )
        self.service = Service.objects.create(
            category=self.category,
            name="Atelier couture",
            created_by=self.user,
            price="90.00",
            duration_minutes=120,
        )
        self.workshop = Workshop.objects.create(
            name="Workshop du samedi",
            address="123 rue principale",
            zip_code="75001",
            city="Paris",
        )
        self.workshop.services.add(self.service)

    def test_workshop_detail_groups_services_by_category(self):
        url = reverse("workshop_detail", args=[self.workshop.pk])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["workshop"], self.workshop)
        services_by_category = response.context["services_by_category"]
        self.assertIn(self.category, services_by_category)
        self.assertEqual(services_by_category[self.category], [self.service])
        self.assertEqual(
            response.context["workshop_photo"],
            "img/elio-santos-5ZQn_gWKvLE-unsplash.jpg",
        )

    def test_workshop_detail_uses_existing_photo(self):
        self.workshop.photo = "custom.jpg"
        self.workshop.save()
        url = reverse("workshop_detail", args=[self.workshop.pk])

        response = self.client.get(url)

        self.assertEqual(response.context["workshop_photo"], "custom.jpg")

    def test_workshop_detail_missing_workshop_returns_404(self):
        url = reverse("workshop_detail", args=[self.workshop.pk + 1])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
