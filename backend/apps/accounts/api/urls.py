from django.urls import path

from apps.accounts.api.views import CsrfView, MeView

urlpatterns = [
    path("csrf", CsrfView.as_view(), name="csrf"),
    path("me", MeView.as_view(), name="me"),
]
