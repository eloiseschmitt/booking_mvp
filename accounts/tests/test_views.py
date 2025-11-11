"""Tests for accounts views."""

# pylint: disable=missing-class-docstring,missing-function-docstring,no-member

from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.constants import PLANNER_HOURS
from accounts.models import Calendar, Category, Event, EventAttendee, Service, Workshop

User = get_user_model()


class DashboardViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com",
            password="safe-password",
            user_type=User.UserType.PROFESSIONAL,
        )
        self.client_user = User.objects.create_user(
            email="client@example.com",
            password="safe-password",
            first_name="Clara",
            last_name="Client",
            user_type=User.UserType.INDIVIDUAL,
            linked_professional=self.user,
        )
        self.calendar = Calendar.objects.create(
            owner=self.user,
            name="Agenda principal",
            slug=f"agenda-{self.user.pk}",
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
        self.assertIn("clients", response.context)
        self.assertEqual(len(response.context["clients"]), 1)
        self.assertEqual(
            response.context["clients"][0]["email"], self.client_user.email
        )
        self.assertIn("client_options", response.context)
        self.assertEqual(len(response.context["client_options"]), 1)
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

        mocked_prepare.assert_called_once_with(42)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["service_form"], mock_form)
        self.assertTrue(response.context["show_service_form"])
        self.assertEqual(response.context["section"], "services")

    def test_dashboard_clients_table_lists_individuals(self):
        self.login()

        response = self.client.get(self.url, {"section": "clients"})

        self.assertEqual(response.status_code, 200)
        clients = response.context["clients"]
        self.assertEqual(len(clients), 1)
        self.assertEqual(clients[0]["full_name"], "Clara Client")
        self.assertEqual(clients[0]["phone"], "—")
        self.assertEqual(clients[0]["email"], self.client_user.email)

    def test_dashboard_clients_table_shows_only_linked_clients(self):
        self.login()
        other_pro = User.objects.create_user(
            email="other-pro@example.com",
            password="safe-password",
            user_type=User.UserType.PROFESSIONAL,
        )
        User.objects.create_user(
            email="other-client@example.com",
            password="safe-password",
            first_name="Olivia",
            last_name="Other",
            user_type=User.UserType.INDIVIDUAL,
            linked_professional=other_pro,
        )

        response = self.client.get(self.url, {"section": "clients"})

        clients = response.context["clients"]
        self.assertEqual(len(clients), 1)
        self.assertEqual(clients[0]["email"], self.client_user.email)
        self.assertTrue(response.context["is_professional"])

    def test_dashboard_clients_section_handles_empty_state(self):
        self.login()
        self.client_user.delete()

        response = self.client.get(self.url, {"section": "clients"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["clients"], [])
        self.assertEqual(response.context["client_options"], [])
        self.assertTrue(response.context["is_professional"])

    def test_dashboard_post_add_client_creates_linked_user(self):
        self.login()
        payload = {
            "action": "add_client",
            "first_name": "Nora",
            "last_name": "New",
            "email": "nora@example.com",
            "phone_number": "0600000000",
        }

        response = self.client.post(self.url, payload)

        self.assertRedirects(response, f"{self.url}?section=clients")
        created = User.objects.get(email="nora@example.com")
        self.assertEqual(created.linked_professional, self.user)
        self.assertEqual(created.user_type, User.UserType.INDIVIDUAL)

    def test_dashboard_post_add_event_creates_event(self):
        self.login()
        service = Service.objects.create(
            category=Category.objects.create(name="Spa"),
            name="Massage duo",
            duration_minutes=90,
            created_by=self.user,
        )
        start_at = timezone.now().replace(minute=0, second=0, microsecond=0)
        response = self.client.post(
            f"{self.url}?section=planning",
            {
                "action": "add_event",
                "start_at": start_at.isoformat(),
                "service_id": service.pk,
                "client_id": self.client_user.pk,
            },
        )

        self.assertRedirects(response, f"{self.url}?section=planning")
        event = Event.objects.get(calendar=self.calendar)
        self.assertEqual(event.title, service.name)
        self.assertEqual(event.created_by, self.user)
        self.assertEqual(
            timezone.localtime(event.start_at).replace(second=0, microsecond=0),
            timezone.localtime(start_at).replace(second=0, microsecond=0),
        )
        self.assertTrue(
            EventAttendee.objects.filter(event=event, user=self.client_user).exists()
        )


class DashboardViewIndividualTests(TestCase):
    def setUp(self):
        self.professional = User.objects.create_user(
            email="pro-owner@example.com",
            password="safe-password",
            user_type=User.UserType.PROFESSIONAL,
        )
        self.user = User.objects.create_user(
            email="client-owner@example.com",
            password="safe-password",
            user_type=User.UserType.INDIVIDUAL,
            linked_professional=self.professional,
        )
        self.url = reverse("dashboard")

    def login(self):
        logged_in = self.client.login(email=self.user.email, password="safe-password")
        self.assertTrue(logged_in)

    def test_add_client_denied_for_individuals(self):
        self.login()

        response = self.client.post(
            self.url,
            {
                "action": "add_client",
                "first_name": "Test",
                "last_name": "User",
                "email": "new@example.com",
            },
        )

        self.assertEqual(response.status_code, 200)
        form = response.context["client_form"]
        self.assertTrue(form.errors)
        self.assertFalse(User.objects.filter(email="new@example.com").exists())

    def test_individual_cannot_add_event(self):
        self.login()
        service = Service.objects.create(
            category=Category.objects.create(name="Yoga"),
            name="Séance test",
            duration_minutes=60,
            created_by=self.user,
        )
        start_at = timezone.now().replace(minute=0, second=0, microsecond=0)
        initial_count = Event.objects.count()

        response = self.client.post(
            f"{self.url}?section=planning",
            {
                "action": "add_event",
                "start_at": start_at.isoformat(),
                "service_id": service.pk,
                "client_id": self.professional.pk,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Event.objects.count(), initial_count)
        self.assertFalse(Event.objects.filter(created_by=self.user).exists())
        self.assertFalse(response.context["is_professional"])

    def test_clients_section_for_individuals_has_no_clients(self):
        self.login()

        response = self.client.get(self.url, {"section": "clients"})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["is_professional"])
        self.assertEqual(response.context["clients"], [])

    def test_dashboard_lists_only_services_created_by_user(self):
        self.login()
        own_category = Category.objects.create(name="Massages détente")
        other_category = Category.objects.create(name="Autres")
        Service.objects.create(
            category=own_category,
            name="Massage relaxant",
            created_by=self.user,
            price="60.00",
            duration_minutes=60,
        )
        other_user = User.objects.create_user(
            email="other@example.com",
            password="safe-password",
            user_type=User.UserType.PROFESSIONAL,
        )
        Service.objects.create(
            category=other_category,
            name="Soin concurrent",
            created_by=other_user,
            price="80.00",
            duration_minutes=90,
        )

        response = self.client.get(self.url, {"section": "services"})

        categories = list(response.context["categories"])
        self.assertEqual(categories, [own_category])
        user_services = response.context["user_services"]
        self.assertEqual(
            [service.name for service in user_services], ["Massage relaxant"]
        )

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
            user_type=User.UserType.PROFESSIONAL,
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
            user_type=User.UserType.PROFESSIONAL,
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
