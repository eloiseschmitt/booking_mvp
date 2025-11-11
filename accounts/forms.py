"""Forms for manipulating categories, services, and clients."""

from django import forms
from django.contrib.auth import get_user_model

from .models import Category, Service

User = get_user_model()


class CategoryForm(forms.ModelForm):
    """Form used to create or update a category."""

    # pylint: disable=too-few-public-methods
    class Meta:
        """Configuration for the category form."""

        model = Category
        fields = ["name"]
        labels = {"name": "Nom de la catégorie"}
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Ex. : Retouches rapides",
                    "maxlength": 100,
                    "class": "kitlast-input",
                }
            )
        }

    def clean_name(self):
        """Ensure the category name is not empty after trimming."""
        name = self.cleaned_data["name"].strip()
        if not name:
            raise forms.ValidationError("Veuillez saisir un nom de catégorie.")
        return name


class ServiceForm(forms.ModelForm):
    """Form used to manage services."""

    # pylint: disable=too-few-public-methods
    class Meta:
        """Configuration for the service form."""

        model = Service
        fields = ["name", "category", "price", "duration_minutes"]
        labels = {
            "name": "Nom de la prestation",
            "category": "Catégorie",
            "price": "Tarif (€)",
            "duration_minutes": "Durée (minutes)",
        }
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Ex. : Pose de bouton",
                    "maxlength": 100,
                    "class": "kitlast-input",
                }
            ),
            "category": forms.Select(attrs={"class": "kitlast-input"}),
            "price": forms.NumberInput(
                attrs={
                    "placeholder": "Ex. : 45",
                    "min": "0",
                    "step": "0.5",
                    "class": "kitlast-input",
                }
            ),
            "duration_minutes": forms.NumberInput(
                attrs={
                    "placeholder": "Ex. : 60",
                    "min": "0",
                    "step": "15",
                    "class": "kitlast-input",
                }
            ),
        }

    def clean_name(self):
        """Ensure the service name is present and within bounds."""
        name = self.cleaned_data["name"].strip()
        if not name:
            raise forms.ValidationError("Veuillez saisir le nom de la prestation.")
        if len(name) > 100:
            raise forms.ValidationError("Le nom ne peut pas dépasser 100 caractères.")
        return name

    def clean_price(self):
        """Prevent negative values for price."""
        price = self.cleaned_data.get("price")
        if price is not None and price < 0:
            raise forms.ValidationError("Le prix doit être positif.")
        return price

    def clean_duration_minutes(self):
        """Prevent negative values for duration."""
        duration = self.cleaned_data.get("duration_minutes")
        if duration is not None and duration < 0:
            raise forms.ValidationError("La durée doit être positive.")
        return duration


class ClientForm(forms.ModelForm):
    """Form used to create customers linked to a professional."""

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "linked_professional",
        ]
        labels = {
            "first_name": "Prénom",
            "last_name": "Nom",
            "email": "Email",
            "phone_number": "Téléphone",
        }
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "kitlast-input"}),
            "last_name": forms.TextInput(attrs={"class": "kitlast-input"}),
            "email": forms.EmailInput(attrs={"class": "kitlast-input"}),
            "phone_number": forms.TextInput(attrs={"class": "kitlast-input"}),
            "linked_professional": forms.HiddenInput(),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Un utilisateur avec cet email existe déjà.")
        return email
