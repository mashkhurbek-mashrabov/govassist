from django.urls import path

from apps.accounts.api.views import CsrfView, MeView, ResendVerificationView

urlpatterns = [
    path("csrf", CsrfView.as_view(), name="csrf"),
    path("me", MeView.as_view(), name="me"),
    path(
        "auth/resend-verification",
        ResendVerificationView.as_view(),
        name="resend-verification",
    ),
]
