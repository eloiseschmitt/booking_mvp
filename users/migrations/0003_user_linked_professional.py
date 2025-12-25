"""Add link between individual users and professionals."""

# pylint: disable=invalid-name

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """Migration to add the linked_professional field."""

    dependencies = [
        ("users", "0002_user_user_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="linked_professional",
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={"user_type": "professional"},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="linked_users",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
