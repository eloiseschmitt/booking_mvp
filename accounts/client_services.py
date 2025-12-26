"""Services for client management (create/update/delete) used by views.

These keep business logic out of the views so handlers remain thin.
"""

from django.utils.crypto import get_random_string

from users.models import User

from .forms import ClientForm


def create_client(user: User, data) -> tuple[bool, User | ClientForm]:
    """Create a client linked to `user`.

    Returns (True, client) on success or (False, form) on failure.
    If the acting user is not a professional, returns a bound form with
    a non-field error explaining the restriction.
    """
    bound = data.copy()
    bound["linked_professional"] = user.pk
    form = ClientForm(bound)

    if not getattr(user, "is_professional", False):
        form.add_error(None, "Vous devez être un professionnel pour ajouter un client.")
        return False, form

    if form.is_valid():
        client = form.save(commit=False)
        client.user_type = User.UserType.INDIVIDUAL
        client.linked_professional = user
        client.set_password(get_random_string(12))
        client.save()
        return True, client

    return False, form


def update_client(user: User, client_id, data) -> tuple[bool, object]:
    """Update a client linked to `user`.

    Returns (True, client) on success, (False, form) if validation fails,
    or (False, None) if the client is not found/authorized.
    """
    client = User.objects.filter(
        pk=client_id,
        linked_professional=user,
        user_type=User.UserType.INDIVIDUAL,
    ).first()
    if not client:
        return False, None

    bound = data.copy()
    # Ensure linked_professional is preserved when not provided in the form data
    if "linked_professional" not in bound or not bound.get("linked_professional"):
        bound["linked_professional"] = (
            client.linked_professional.pk if client.linked_professional else ""
        )
    form = ClientForm(bound, instance=client)
    if form.is_valid():
        form.save()
        return True, client
    return False, form


def delete_client(user: User, client_id) -> tuple[bool, str | None]:
    """Delete a client linked to `user`.

    Returns (True, None) on success, or (False, message) on failure.
    """
    client = User.objects.filter(
        pk=client_id,
        linked_professional=user,
        user_type=User.UserType.INDIVIDUAL,
    ).first()
    if not client:
        return False, "Client introuvable ou non autorisé."
    client.delete()
    return True, None
