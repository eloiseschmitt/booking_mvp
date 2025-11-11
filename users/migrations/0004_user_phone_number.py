"""Add phone number field to user."""

# pylint: disable=invalid-name

from django.db import migrations, models


class Migration(migrations.Migration):
    """Migration for adding phone field."""

    dependencies = [
        ("users", "0003_user_linked_professional"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="phone_number",
            field=models.CharField(blank=True, max_length=30),
        ),
    ]
