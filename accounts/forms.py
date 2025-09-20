from django import forms

from .models import Category


class CategoryForm(forms.ModelForm):
    class Meta:
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
        name = self.cleaned_data["name"].strip()
        if not name:
            raise forms.ValidationError("Veuillez saisir un nom de catégorie.")
        return name
