from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def is_admin(user):
    """Superuser or a user whose Profile.role is 'admin'."""
    if user.is_superuser:
        return True
    profile = getattr(user, "profile", None)
    return bool(profile and profile.role == "admin")


def admin_required(view):
    """Login needed + must be admin. Staff users get redirected."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not is_admin(request.user):
            messages.error(request, "Only admin can open that page.")
            return redirect("dashboard")
        return view(request, *args, **kwargs)

    return login_required(wrapper)
