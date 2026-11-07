from .decorators import is_admin


def role(request):
    """Makes `is_admin` available in every template (used to hide menu links)."""
    return {"is_admin": request.user.is_authenticated and is_admin(request.user)}
