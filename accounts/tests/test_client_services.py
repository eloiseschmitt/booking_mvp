"""Unit tests for accounts.client_services."""

from django.test import TestCase

from django.contrib.auth import get_user_model

from accounts.client_services import create_client, update_client, delete_client

User = get_user_model()


class ClientServicesTests(TestCase):
    def setUp(self):
        self.professional = User.objects.create_user(
            email="pro@example.com",
            password="pw",
            user_type=User.UserType.PROFESSIONAL,
        )
        # Individual users must be linked to a professional per model validation.
        self.individual = User.objects.create_user(
            email="individual@example.com",
            password="pw",
            user_type=User.UserType.INDIVIDUAL,
            linked_professional=self.professional,
        )

    def test_create_client_by_professional_creates_user(self):
        payload = {
            "first_name": "Test",
            "last_name": "User",
            "email": "new-client@example.com",
            "phone_number": "0600000000",
        }
        success, result = create_client(self.professional, payload)
        self.assertTrue(success)
        self.assertIsNotNone(result.pk)
        self.assertEqual(result.linked_professional, self.professional)
        self.assertEqual(result.user_type, User.UserType.INDIVIDUAL)

    def test_create_client_denied_for_individual(self):
        payload = {"first_name": "X", "email": "x@example.com"}
        success, form = create_client(self.individual, payload)
        self.assertFalse(success)
        # Expect a non-field error explaining permission
        self.assertTrue(hasattr(form, "non_field_errors"))
        self.assertTrue(form.non_field_errors())

    def test_update_client_success(self):
        client = User.objects.create_user(
            email="client1@example.com",
            password="pw",
            user_type=User.UserType.INDIVIDUAL,
            linked_professional=self.professional,
            first_name="Old",
        )
        payload = {"first_name": "New", "email": client.email}
        success, result = update_client(self.professional, client.pk, payload)
        self.assertTrue(success)
        client.refresh_from_db()
        self.assertEqual(client.first_name, "New")

    def test_update_client_not_found_or_unauthorized(self):
        # Using an ID that doesn't exist
        success, result = update_client(self.professional, 99999, {"first_name": "X"})
        self.assertFalse(success)
        self.assertIsNone(result)

    def test_delete_client_success_and_failure(self):
        client = User.objects.create_user(
            email="client2@example.com",
            password="pw",
            user_type=User.UserType.INDIVIDUAL,
            linked_professional=self.professional,
        )
        success, message = delete_client(self.professional, client.pk)
        self.assertTrue(success)
        self.assertIsNone(message)
        self.assertFalse(User.objects.filter(pk=client.pk).exists())

        # attempt to delete non-existing / unauthorized
        success2, message2 = delete_client(self.professional, 99999)
        self.assertFalse(success2)
        self.assertIsNotNone(message2)
