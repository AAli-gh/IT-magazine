from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


class AdminMFAMiddleware:
    """Require staff to set up two-factor authentication before using the admin panel.

    Admin logins go through allauth (see config/urls.py), which asks for the
    authenticator code; this middleware makes sure every staff account has one.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            settings.ADMIN_REQUIRE_MFA
            and request.path.startswith("/admin/")
            and request.user.is_authenticated
            and request.user.is_staff
            and not self._has_mfa(request.user)
        ):
            messages.warning(request, "برای ورود به پنل مدیریت، ابتدا ورود دومرحله‌ای را فعال کنید.")
            return redirect(f"{reverse('mfa_activate_totp')}?next={request.path}")
        return self.get_response(request)

    @staticmethod
    def _has_mfa(user):
        from allauth.mfa.models import Authenticator

        return Authenticator.objects.filter(user=user, type=Authenticator.Type.TOTP).exists()
