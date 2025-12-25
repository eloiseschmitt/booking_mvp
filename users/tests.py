"""Tests for the users application."""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase


class UserLinkedProfessionalTests(TestCase):
    """Ensure user/professional relationships are enforced."""

    def setUp(self):
        """Set up data used by the tests."""
        self.user_model = get_user_model()
        self.professional = self.user_model.objects.create_user(
            email="pro@example.com",
            password="safe-password",
            user_type=self.user_model.UserType.PROFESSIONAL,
        )

    def test_individual_requires_professional(self):
        """An individual must reference a professional user."""
        client = self.user_model(
            email="client@example.com",
            user_type=self.user_model.UserType.INDIVIDUAL,
            linked_professional=self.professional,
        )
        client.set_password("safe-password")
        client.save()
        self.assertEqual(client.linked_professional, self.professional)

        invalid_client = self.user_model(
            email="invalid@example.com",
            user_type=self.user_model.UserType.INDIVIDUAL,
        )
        invalid_client.set_password("safe-password")
        with self.assertRaises(ValidationError):
            invalid_client.save()

    def test_professional_must_link_only_to_professional(self):
        """Professionals may link to another professional but not to individuals."""
        other_pro = self.user_model.objects.create_user(
            email="mentor@example.com",
            password="safe-password",
            user_type=self.user_model.UserType.PROFESSIONAL,
        )
        self.professional.linked_professional = other_pro
        self.professional.save()
        self.assertEqual(self.professional.linked_professional, other_pro)

        client = self.user_model.objects.create_user(
            email="client-two@example.com",
            password="safe-password",
            user_type=self.user_model.UserType.INDIVIDUAL,
            linked_professional=self.professional,
        )
        other_pro.linked_professional = client
        with self.assertRaises(ValidationError):
            other_pro.save()
