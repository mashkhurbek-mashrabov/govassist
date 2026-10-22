from django.urls import path

from apps.common.api.views import HealthView

urlpatterns = [path("health", HealthView.as_view(), name="health")]
