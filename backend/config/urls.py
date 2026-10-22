from django.conf import settings
from django.contrib import admin
from django.urls import include, path

api_v1 = [
    path("", include("apps.common.api.urls")),
    path("", include("apps.accounts.api.urls")),
    path("", include("apps.geo.api.urls")),
    path("", include("apps.chat.api.urls")),
]

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("_allauth/", include("allauth.headless.urls")),
    path("api/v1/", include(api_v1)),
]
