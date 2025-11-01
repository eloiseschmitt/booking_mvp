"""Tests for service helper utilities."""

# pylint: disable=missing-class-docstring,missing-function-docstring,no-member

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.forms import ServiceForm
from accounts.models import Category, Service
from accounts.services import delete_service, prepare_service_form, save_service_form

User = get_user_model()


class ServiceHelpersTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="service-owner@example.com",
            password="safe-password",
            user_type=User.UserType.PROFESSIONAL,
        )
        self.category = Category.objects.create(name="Test")

    def test_prepare_service_form_without_id(self):
        form, service = prepare_service_form()
        self.assertIsNone(service)
        self.assertFalse(form.is_bound)

    def test_prepare_service_form_with_id(self):
        service = Service.objects.create(
            category=self.category,
            name="Massage",
            created_by=self.user,
        )
        form, instance = prepare_service_form(service.pk)
        self.assertEqual(instance, service)
        self.assertEqual(form.instance, service)

    def test_save_service_form_success(self):
        form = ServiceForm(
            data={
                "name": "Soin visage",
                "category": self.category.pk,
                "price": "50.00",
                "duration_minutes": 60,
            }
        )
        success, saved_form = save_service_form(form, user=self.user)
        self.assertTrue(success)
        self.assertEqual(saved_form.instance.created_by, self.user)

    def test_save_service_form_invalid(self):
        form = ServiceForm(data={"name": "", "category": self.category.pk})
        success, returned_form = save_service_form(form, user=self.user)
        self.assertFalse(success)
        self.assertIn("name", returned_form.errors)

    def test_delete_service(self):
        service = Service.objects.create(
            category=self.category,
            name="Supprimable",
            created_by=self.user,
        )
        service_id = service.pk
        deleted = delete_service(service_id)
        self.assertIsNone(deleted.pk)
        self.assertIsInstance(deleted, Service)
        self.assertFalse(Service.objects.filter(pk=service_id).exists())
