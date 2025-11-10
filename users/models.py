"""User model and manager definitions."""

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom manager to support email-based authentication."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and persist a user with the given credentials."""
        if not email:
            raise ValueError("Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create a standard user."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """Create an administrative superuser."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Application user based on email as the primary identifier."""

    # pylint: disable=too-many-ancestors
    class UserType(models.TextChoices):
        """User types available in the system."""

        PROFESSIONAL = "professional", "Professionnel"
        INDIVIDUAL = "individual", "Particulier"

    email = models.EmailField("email address", unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices,
        default=UserType.INDIVIDUAL,
    )
    linked_professional = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="linked_users",
        limit_choices_to={"user_type": UserType.PROFESSIONAL},
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    def __str__(self) -> str:
        return str(self.email)

    @property
    def is_professional(self):
        """Return whether the user is a professional."""
        return self.user_type == self.UserType.PROFESSIONAL

    def clean(self):
        super().clean()
        if self.user_type == self.UserType.INDIVIDUAL:
            if not self.linked_professional:
                raise ValidationError(
                    {
                        "linked_professional": "Un particulier doit être rattaché à un professionnel."
                    }
                )
            if self.linked_professional.user_type != self.UserType.PROFESSIONAL:
                raise ValidationError(
                    {
                        "linked_professional": "Le compte associé doit être professionnel."
                    }
                )
        elif (
            self.linked_professional
            and self.linked_professional.user_type != self.UserType.PROFESSIONAL
        ):
            raise ValidationError(
                {"linked_professional": "Le compte associé doit être professionnel."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
